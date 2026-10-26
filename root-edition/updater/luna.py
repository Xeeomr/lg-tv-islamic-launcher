"""One bounded Luna call with stdin kept open for the firmware client."""
import json
import os
import select
import subprocess
import time


def call(uri,payload,timeout=15):
    p=subprocess.Popen(['/usr/bin/luna-send','-n','1',uri,json.dumps(payload)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        end=time.monotonic()+timeout;raw=b''
        while time.monotonic()<end:
            if not select.select([p.stdout],[],[],max(0,end-time.monotonic()))[0]:break
            chunk=os.read(p.stdout.fileno(),4096)
            if not chunk:break
            raw+=chunk
            if len(raw)>65536:raise ValueError('Oversized bus reply')
            try:reply=json.loads(raw)
            except ValueError:continue
            if not isinstance(reply,dict) or reply.get('returnValue') is not True:raise RuntimeError('Bus operation rejected')
            return reply
        raise TimeoutError('Bus response timed out')
    finally:
        if p.poll() is None:p.terminate()
        try:p.communicate(timeout=1)
        except subprocess.TimeoutExpired:p.kill();p.communicate()
