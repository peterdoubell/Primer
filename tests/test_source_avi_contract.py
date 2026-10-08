"""AVI sample tables bind actual source frames, not an inferred clinical clock."""
import struct,subprocess,json,shutil
from pathlib import Path
import pytest
from primer.source_motion_contract import parse_avi_contract
ROOT=Path(__file__).resolve().parents[1]
CACHE=Path('/Users/peter/Documents/ChatGPT/Primer/.research/tinnitus-clinical-source-review/PMC5263210')
def chunk(tag,raw):return tag+struct.pack('<I',len(raw))+raw+(b'\0' if len(raw)&1 else b'')
def sample():
 main=struct.pack('<14I',333333,0,0,0x10,2,0,1,0,10,8,0,0,0,0)
 stream=bytearray(56);stream[:4]=b'vids';struct.pack_into('<4I',stream,20,1,3,0,2);struct.pack_into('<4h',stream,48,0,0,10,8)
 bitmap=struct.pack('<IiiHH4s5I',40,10,8,1,16,b'CRAM',0,0,0,0,0)
 header=chunk(b'LIST',b'hdrl'+chunk(b'avih',main)+chunk(b'LIST',b'strl'+chunk(b'strh',bytes(stream))+chunk(b'strf',bitmap)))
 a=chunk(b'00db',b'abcd');b=chunk(b'00db',b'efgh');movie=chunk(b'LIST',b'movi'+a+b);index=chunk(b'idx1',struct.pack('<4sIII',b'00db',0x10,4,4)+struct.pack('<4sIII',b'00db',0x10,4+len(a),4));body=b'AVI '+header+movie+index
 return b'RIFF'+struct.pack('<I',len(body))+body
def test_source_tables_determine_chronology():
 assert parse_avi_contract(sample())=={'width':10,'height':8,'frames':2,'pts_seconds':[0,1/3]}
@pytest.mark.parametrize('change',['truncated','bad_riff_size','bad_chunk_size','extra_track','shifted_start','frame_count','clock','scaled_rect','bitmap','wrong_offset','nonkey_frame','extra_continuation'])
def test_untrusted_or_ambiguous_container_rejected(change):
 data=bytearray(sample())
 if change=='truncated':data=data[:-3]
 if change=='bad_riff_size':struct.pack_into('<I',data,4,len(data)+100)
 if change=='bad_chunk_size':struct.pack_into('<I',data,data.index(b'strf')+4,999999)
 if change=='extra_track':struct.pack_into('<I',data,data.index(b'avih')+8+24,2)
 if change=='shifted_start':struct.pack_into('<I',data,data.index(b'strh')+8+28,1)
 if change=='frame_count':struct.pack_into('<I',data,data.index(b'strh')+8+32,3)
 if change=='clock':struct.pack_into('<I',data,data.index(b'avih')+8,200000)
 if change=='scaled_rect':struct.pack_into('<h',data,data.index(b'strh')+8+52,9)
 if change=='bitmap':struct.pack_into('<i',data,data.index(b'strf')+8+4,9)
 if change=='wrong_offset':struct.pack_into('<I',data,data.index(b'idx1')+8+8,20)
 if change=='nonkey_frame':struct.pack_into('<I',data,data.index(b'idx1')+8+4,0)
 if change=='extra_continuation':data+=b'RIFF'+b'\0'*20
 with pytest.raises(ValueError):parse_avi_contract(data)
def test_original_container_matches_independent_probe_if_available():
 if not CACHE.exists() or not shutil.which('ffprobe'):pytest.skip('Original source cache/ffprobe unavailable')
 for number in [1,2]:
  path=CACHE/f'40134_2017_199_MOESM{number}_ESM.avi';contract=parse_avi_contract(path)
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_frames','-of','json',str(path)]));s=probe['streams'][0]
  assert (contract['width'],contract['height'],contract['frames'])==(s['width'],s['height'],int(s['nb_frames']))==(1024,1024,12)
  assert [float(r['best_effort_timestamp_time']) for r in probe['frames']]==pytest.approx(contract['pts_seconds'],abs=1e-6)
