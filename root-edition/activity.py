"""Root installer controls only the candidate's fixed recovery activity."""
import json,os,select,subprocess,time
from pathlib import Path
NAME='com.cleanyourtv.root.preview.service'
SENDER='com.webos.lunasend-cytvrootrecovery'
STATE=Path('/var/lib/clean-your-tv-root')

def call(method,payload):
    if method not in ('list','create','cancel'):raise ValueError('Unsupported activity operation')
    p=subprocess.Popen(['/usr/bin/luna-send','-m',SENDER,'-n','1','luna://com.palm.activitymanager/'+method,json.dumps(payload)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        data=b'';end=time.monotonic()+15
        while time.monotonic()<end:
            if not select.select([p.stdout],[],[],max(0,end-time.monotonic()))[0]:break
            chunk=os.read(p.stdout.fileno(),65536)
            if not chunk:break
            data+=chunk
            if len(data)>2097152:raise ValueError('Activity reply too large')
            try:reply=json.loads(data)
            except ValueError:continue
            if reply.get('returnValue') is not True:raise ValueError('Activity '+method+': '+str(reply))
            return reply
        raise TimeoutError('Activity '+method)
    finally:
        if p.poll() is None:p.terminate()
        try:p.communicate(timeout=1)
        except subprocess.TimeoutExpired:p.kill();p.communicate()

def manage(method,secure,write):
    if os.geteuid()!=0:raise PermissionError('Root required')
    if method not in ('register','unregister'):raise ValueError('Invalid operation')
    spec=json.loads(secure(STATE/'service/activity.json'))
    if spec.get('name')!=NAME+'.recovery' or spec.get('callback',{}).get('method')!='luna://'+NAME+'/boot':raise ValueError('Unexpected recovery activity')
    def listing():
        values=call('list',dict(details=True,subscribers=True,current=False,internal=False)).get('activities')
        if not isinstance(values,list):raise ValueError('Invalid activity list')
        matches=[x for x in values if x.get('name')==spec['name']]
        if len(matches)>1:raise ValueError('Duplicate recovery activity')
        for item in matches:
            if item.get('creator')!={'serviceId':SENDER} or any(item.get(k)!=spec[k] for k in ('callback','trigger')) or any(item.get('type',{}).get(k)!=v for k,v in spec['type'].items()):raise ValueError('Foreign recovery activity')
        return matches
    matches=listing()
    # Intent is durable before submission; unknown responses are inspected by name.
    receipt=STATE/'activity-registration.json'
    expected={'creator':SENDER,'activity':spec}
    if receipt.exists() and json.loads(secure(receipt))!=expected:raise ValueError('Activity receipt drift')
    if not receipt.exists():write(receipt,json.dumps(expected).encode())
    if method=='register' and not matches:call('create',{'activity':spec,'start':True,'replace':False})
    if method=='unregister' and matches:call('cancel',{'activityId':matches[0]['activityId']})
    found=listing()
    if bool(found)!=(method=='register'):raise ValueError('Activity readback mismatch')
    return {'returnValue':True,'root':True,'registered':bool(found),'activityName':spec['name']}
