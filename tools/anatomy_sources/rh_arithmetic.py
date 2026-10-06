"""Independent ECMA-363 16-bit interval reader for cross-checking recovery."""
class Frequencies:
 def __init__(self,limit=8191):
  self.limit=limit;self.freq={0:1};self.total=1;self.tree=[0]*65537;self._increment(0,1)
 def _increment(self,s,n):
  i=s+1
  while i<=65536:self.tree[i]+=n;i+=i&-i
 def add_symbol(self,s):
  if s>65535:return
  if self.total>=self.limit:
   self.freq={k:v//2 for k,v in self.freq.items() if v//2};self.freq[0]=self.freq.get(0,0)+1;self.total=sum(self.freq.values());self.tree=[0]*65537
   for k,v in self.freq.items():self._increment(k,v)
  self.freq[s]=self.freq.get(s,0)+1;self.total+=1;self._increment(s,1)
 def prefix(self,s):
  out=0
  while s:out+=self.tree[s];s-=s&-s
  return out
 def lookup(self,v):
  if not 0<=v<self.total:raise ValueError('Bad cumulative frequency')
  i=0;step=65536
  while step:
   j=i+step
   if j<=65536 and self.tree[j]<=v:v-=self.tree[j];i=j
   step//=2
  return i
class BitStream:
 def __init__(self,data):self.data=data+b'\0'*16;self.cursor=0;self.low=0;self.high=65535;self.underflow=0;self.contexts={}
 def bit(self,p):
  if p>=len(self.data)*8:raise ValueError('Arithmetic input exhausted')
  return (self.data[p//8]>>(p%8))&1
 def read_symbol(self,context):
  code=self.bit(self.cursor)
  for i in range(15):code=code*2+self.bit(self.cursor+1+self.underflow+i)
  span=self.high-self.low+1
  if context>1024:total=context-1024;h=None
  else:
   if context not in self.contexts:self.contexts[context]=Frequencies()
   h=self.contexts[context];total=h.total
  cumulative=(total*(code-self.low+1)-1)//span
  if h is None:symbol=cumulative+1;prefix=cumulative;frequency=1
  else:symbol=h.lookup(cumulative);prefix=h.prefix(symbol);frequency=h.freq[symbol]
  start=self.low;self.high=start+(span*(prefix+frequency))//total-1;self.low=start+(span*prefix)//total
  if h is not None:h.add_symbol(symbol)
  leading=0
  while (self.low^self.high)<32768:
   self.low=(self.low*2)&65535;self.high=(self.high*2+1)&65535;leading+=1
  if leading:self.cursor+=leading+self.underflow;self.underflow=0
  while self.low&16384 and not self.high&16384:
   self.low=(self.low&16383)*2;self.high=(self.high&16383)*2+32769;self.underflow+=1
  return symbol
 def read_u8(self):
  if self.low==0 and self.high==65535 and self.underflow==0:
   out=sum(self.bit(self.cursor+i)<<i for i in range(8));self.cursor+=8;return out
  value=self.read_symbol(1024+256)-1
  return int(f'{value:08b}'[::-1],2)
 def read_u16(self):return self.read_u8()+256*self.read_u8()
 def read_u32(self):return self.read_u16()+65536*self.read_u16()
