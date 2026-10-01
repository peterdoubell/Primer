"""Read pinned ZIP/ZIP64 source members by validated ranges; no extraction paths."""
import io
import struct
import zipfile
import zlib
from urllib.request import Request,urlopen


class RemoteZipSource:
    def __init__(self,url,size):
        self.url=url;self.size=size;self.etag=None
        tail=self.fetch(max(0,size-65557),size-1)
        at=tail.rfind(b'PK\x05\x06')
        if at<0:raise ValueError('No ZIP end record')
        _,disk,central_disk,on_disk,total,length,offset,comment=struct.unpack_from('<4s4H2LH',tail,at)
        if disk or central_disk or on_disk!=total:raise ValueError('Multipart archive unsupported')
        if total==65535 or length==0xffffffff or offset==0xffffffff:
            locator_at=at-20
            if locator_at<0 or tail[locator_at:locator_at+4]!=b'PK\x06\x07':raise ValueError('Missing ZIP64 locator')
            _,locator_disk,record_offset,disks=struct.unpack_from('<4sLQL',tail,locator_at)
            if locator_disk or disks!=1:raise ValueError('Multipart ZIP64 unsupported')
            record=self.fetch(record_offset,record_offset+55)
            fields=struct.unpack('<4sQ2H2L4Q',record)
            if fields[0]!=b'PK\x06\x06' or fields[4] or fields[5] or fields[6]!=fields[7]:raise ValueError('Invalid ZIP64 directory')
            total,length,offset=fields[7],fields[8],fields[9]
        central=self.fetch(offset,offset+length-1)
        # Parsing directory only: synthetic local offsets are never used to
        # fetch members. ZipInfo retains their original central-directory offsets.
        if total>=65535:raise ValueError('Source inventory too large for directory-only parser')
        footer=struct.pack('<4s4H2LH',b'PK\x05\x06',0,0,total,total,len(central),0,0)
        parsed=zipfile.ZipFile(io.BytesIO(central+footer))
        self.entries={item.filename:item for item in parsed.infolist()}
        if len(self.entries)!=total:raise ValueError('Duplicate or incomplete source inventory')
        self.central_directory=central

    def fetch(self,start,stop):
        if not 0<=start<=stop<self.size:raise ValueError('Range leaves source archive')
        with urlopen(Request(self.url,headers={'Range':f'bytes={start}-{stop}'}),timeout=60) as response:
            if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {start}-{stop}/{self.size}':raise ValueError('Unverified source range')
            tag=response.headers.get('ETag')
            if not tag or self.etag is not None and tag!=self.etag:raise ValueError('Source archive identity changed or missing')
            self.etag=tag;data=response.read(stop-start+2)
        if len(data)!=stop-start+1:raise ValueError('Source range length differs')
        return data

    def member(self,name):
        entry=self.entries[name]
        if entry.is_dir() or entry.file_size>512*1024*1024:raise ValueError('Unsupported member scope')
        header=self.fetch(entry.header_offset,entry.header_offset+29)
        sig,ver,flags,method,mtime,mdate,crc,csize,usize,nlen,xlen=struct.unpack('<4s5H3L2H',header)
        if sig!=b'PK\x03\x04' or flags&1 or method!=entry.compress_type:raise ValueError('Invalid member header')
        raw_name=self.fetch(entry.header_offset+30,entry.header_offset+29+nlen)
        if raw_name.decode('utf-8' if flags&0x800 else 'cp437')!=name:raise ValueError('Local and central member names differ')
        begin=entry.header_offset+30+nlen+xlen
        data=self.fetch(begin,begin+entry.compress_size-1)
        if method==8:data=zlib.decompress(data,-15)
        elif method!=0:raise ValueError('Unsupported source compression')
        if len(data)!=entry.file_size or zlib.crc32(data)&0xffffffff!=entry.CRC:raise ValueError('Member checksum or size mismatch')
        return data
