import io, pathlib, tarfile, sys
# Rewrites the ar archive in Python: macOS BSD `ar r` turns the Debian-style ipk into a symbol-table-only archive.
def read_ar(b):
 assert b[:8]==b'!<arch>\n','not an ar archive'
 i,members=8,[]
 while i<len(b):
  h=b[i:i+60];size=int(h[48:58]);members.append([h[:16].decode().strip().rstrip('/'),h,b[i+60:i+60+size]]);i+=60+size+(size&1)
 return members
def write_ar(members):
 out=bytearray(b'!<arch>\n')
 for name,h,data in members:out+=h[:48]+str(len(data)).ljust(10).encode()+h[58:]+data+(b'\n' if len(data)&1 else b'')
 return bytes(out)
p=pathlib.Path(sys.argv[1]).resolve()
members=read_ar(p.read_bytes());data=next(m for m in members if m[0]=='data.tar.gz')
out=io.BytesIO(); changed=[]
with tarfile.open(fileobj=io.BytesIO(data[2]),mode='r:gz') as src,tarfile.open(fileobj=out,mode='w:gz') as dst:
 for entry in src:
  name=entry.name.rstrip('/')
  if name.endswith('/com.local.nativehome/state') or name.endswith('/com.local.nativehome.service/state'):
   assert entry.isdir()
   entry.uid=5999;entry.gid=5000;entry.uname='prisoner';entry.gname='jailer';entry.mode=0o770
   changed.append(name)
  dst.addfile(entry,src.extractfile(entry) if entry.isfile() else None)
assert len(changed)==2,changed
data[2]=out.getvalue();p.write_bytes(write_ar(members))
print('Set owner prisoner:jailer and mode 0770 for data directories:',changed)
