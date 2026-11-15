#!/usr/bin/env python3
"""Experimental RH geometry interpretation; source ambiguities remain explicit holds.

Functional implementation from Adobe U3D Supported Elements (Acrobat 8.1 SDK)
and ECMA-363. No third-party decoder code is bundled. UIC1 bootstrap and opaque
normal attributes remain unverified; this must not grant clinical model coverage.
"""
import struct
import hashlib
from tools.anatomy_sources.rh_arithmetic import BitStream

class R:
 def __init__(self,b):self.b=b;self.p=0;self.log=[];self.float_blocks=[]
 def take(self,n):
  if self.p+n>len(self.b):raise ValueError('Truncated data')
  v=self.b[self.p:self.p+n];self.p+=n;return v
 def u(self,n=1):return int.from_bytes(self.take(n),'little')
 def f(self):return struct.unpack('<f',self.take(4))[0]
 def ints(self,count,maximum,vertical=False):
  offset=self.p;t=self.u();typ=t&63
  if typ==0:v=[0]*count
  elif typ==1:v=[self.u(4)]*count
  elif typ==2:
   size=self.u((t>>6)+1);assert size==(count+1)//2;buf=self.take(size);v=[(buf[i//2]>>(4*(i%2)))&15 for i in range(count)]
  elif typ in range(3,7):
   size=self.u((t>>6)+1);assert size==count*(typ-2);v=[self.u(typ-2) for _ in range(count)]
  elif typ in [7,8,9,10]:
   size=self.u((t>>6)+1);buf=self.take(size)
   if typ==9:
    bs=BitStream(buf);v=[]
    for i in range(count):
     sym=bs.read_symbol(1)
     if sym:a=sym-1
     else:
      a=bs.read_u16() if maximum<=65535 else bs.read_u32();bs.contexts[1].add_symbol(a+1)
     v.append(a)
   elif typ==10:v=uic(buf,count,True)
   elif typ==7:v=rh39(buf,count)
   else:
    bs=BitStream(buf);v=[bs.read_symbol(0x400+maximum+1)-1 for _ in range(count)]
  else:raise ValueError('Unknown integer codec '+str(typ))
  if len(v)!=count or any(not 0<=i<=maximum for i in v):raise ValueError('Decoded integer range differs '+str((typ,count,maximum,min(v),max(v))))
  self.log.append({'start':offset,'end':self.p,'codec':typ,'count':count,'maximum':maximum,'source_encoded_span_sha256':hashlib.sha256(self.b[offset:self.p]).hexdigest(),'values_sha256':hashlib.sha256(struct.pack('<'+'I'*len(v),*v)).hexdigest()})
  return v
 def floats(self,count,dimensions):
  if count==0:return []
  start=self.p;typ=self.u();axes=[];controls=[]
  if typ==0:axes=[[self.f() for _ in range(count)] for _ in range(dimensions)]
  elif typ==2:
   for i in range(dimensions):
    mn=self.f();mx=self.f()
    if mn==mx:axes.append([mn]*count);controls.append({'minimum':mn,'maximum':mx,'quant_count':None})
    else:
     n=self.u(4);q=self.ints(count,n);axes.append([mn+x*(mx-mn)/n for x in q]);controls.append({'minimum':mn,'maximum':mx,'quant_count':n})
  elif not count:return []
  else:raise ValueError('Unknown float datatype '+str(typ))
  self.float_blocks.append({'start':start,'end':self.p,'count':count,'dimensions':dimensions,'datatype':typ,'axis_controls':controls,'source_span_sha256':hashlib.sha256(self.b[start:self.p]).hexdigest()})
  return list(zip(*axes))
def uic(buf,count,vertical,initial_values=None):
 values=[(-i)%32 for i in range(32)] if initial_values is None else list(initial_values)
 if len(values)!=32 or any(not isinstance(v,int) or not 0<=v<=0xffffffff for v in values):raise ValueError('Invalid experimental history')
 r=R(buf);deltas=[0]*32;vp=dp=0;queue=0;qi=0;cur=0;out=[]
 def back(i):return values[(vp-i)%32]
 for i in range(count):
  prev=cur;vert=out[i-3] if vertical and i>=3 else (0 if vertical else cur)
  if queue:queue-=1;cur=back(qi)
  else:
   c=r.u();op=c&15;a=c>>4
   if op==0:cur=back(a)
   elif op==5:cur=back(16+a)
   elif op==13:cur=back(a>>2);queue=1;qi=a&3
   elif op==14:cur=back(0);queue=a+2;qi=0
   elif op==6:cur+=deltas[(dp-a)%32]
   elif op==1:cur+=(a>>1)+1 if a&1 else -((a>>1)+1)
   elif op==3:cur=vert+a+1
   elif op==4:cur=vert-a-1
   elif op==7:cur=vert+a+17
   elif op==8:cur=vert-a-17
   elif op==9:cur+=a+(r.u()<<4)+3
   elif op==10:cur-=a+(r.u()<<4)+3
   elif op==11:cur=a+(r.u()<<4)
   elif op==12:cur=a+(r.u(2)<<4)
   elif op==15:
    constants=[0,1,2,3,4,255,0xff00,0xff0000,0xff000000,0xffffff,0xffffffff]
    if a<len(constants):cur=constants[a]
    elif a==11:cur=r.u(3)
    elif a==12:cur=r.u(4)
    elif a==13:queue=r.u(2)+36;qi=0
    else:raise ValueError('Unknown extended UIC command')
   else:raise ValueError('Unknown UIC command')
  if cur<0:raise ValueError('Negative UIC value '+str((i,r.p,prev,vert,queue,qi,cur,buf[max(0,r.p-15):r.p+15].hex())))
  cur&=0xffffffff;vp=(vp+1)%32;values[vp]=cur
  delta=cur-prev
  if delta and abs(delta)<0x7fffffff:dp=(dp+1)%32;deltas[dp]=delta
  out.append(cur)
 if queue or r.p!=len(buf):raise ValueError('Unconsumed UIC data '+str((queue,r.p,len(buf))))
 return out
def rh39(buf,count):
 r=R(buf);out=[];offset=0
 while len(out)<count:
  c=r.u();op=(c>>4)&7;n=(c&15)
  n=17+(n<<8)+r.u() if c&128 else n+1
  if op==7:offset=r.u(n);continue
  if len(out)+n>count:raise ValueError('RH39 overflow '+str((r.p,len(buf),len(out),n,count,op,buf[max(0,r.p-10):r.p+10].hex())))
  if op==1:
   b=r.take((n+1)//2);v=[offset+((b[i//2]>>(4*(i%2)))&15) for i in range(n)]
  elif op==5:v=[offset]*n
  else:
   widths={0:4,2:1,3:2,4:2,6:1};v=[r.u(widths[op])+(offset if op in [2,3] else 0) for _ in range(n)]
  out+=v
 if r.p!=len(buf):raise ValueError('RH39 trailing data')
 return out
def decode(buf):
 r=R(buf);name=r.take(r.u(2)).decode();flags=r.u();mc=r.u({1:1,2:2,3:4}[flags>>6]) if flags>>6 else 1
 if flags&63:raise ValueError('Unsupported resource flags')
 mats=[]
 for i in range(mc):
  mf=r.u();layers=r.u(((mf>>4)&3)+1);shading=r.u(((mf>>2)&3)+1)
  if layers:r.take(max(0,(layers-1+3)//4))
  mats.append((mf,layers,shading))
 vf=r.u();width=(vf>>6)+1;counts=[r.u(width) if vf&(1<<i) else 0 for i in range(6)];nf,np,nn,nd,ns,nt=counts
 p=r.floats(np,3);normal_type=r.b[r.p];normal_quants=normal_codec=normal_size=0;normal_data=b''
 if normal_type==3:
  r.u();normal_quants=r.u(4);normal_codec=r.u();normal_size=r.u((normal_codec>>6)+1);normal_data=r.take(normal_size);normals=[]
 else:normals=r.floats(nn,3)
 diff=r.floats(nd,4);spec=r.floats(ns,4);tex=r.floats(nt,4)
 mi=[0]*nf if mc==1 else r.ints(nf,mc-1);pi=r.ints(nf*3,np-1,True);ni=r.ints(nf*3,nn-1,True)
 if nd or ns or nt:raise ValueError('Extra source indices need support')
 if r.p!=len(buf):raise ValueError('Mesh trailing data '+str((r.p,len(buf))))
 return {'name':name,'counts':counts,'positions':p,'normal_payload_not_decoded':{'type':normal_type,'quants':normal_quants,'codec':normal_codec&63,'bytes':normal_size,'sha256':hashlib.sha256(normal_data).hexdigest()},'normals':normals,'material_indices':mi,'faces':[pi[i:i+3] for i in range(0,len(pi),3)],'normal_indices':ni,'integer_blocks':r.log,'float_blocks':r.float_blocks,'source_payload_sha256':hashlib.sha256(buf).hexdigest(),'source_payload_bytes_accounted':r.p,'normal_attributes_decoded':bool(normals),'uic1_bootstrap_independently_verified':False,'clinical_approval':False,'runtime_promoted':False}
