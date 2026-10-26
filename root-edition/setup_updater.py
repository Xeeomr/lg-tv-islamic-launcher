#!/usr/bin/env python3
"""Review or apply one-time Root Updater setup through explicit root SSH."""
import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import uuid


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True);parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--ssh');parser.add_argument('--identity',type=Path);parser.add_argument('--apply',action='store_true')
    parser.add_argument('--device',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--python',default='/usr/bin/python3',choices=('/usr/bin/python3','/var/lib/clean-your-tv-python/4a71641c8d5536175e404a961624e8656eba30e97b5026f6bd7dc31e4bbeaaea/bin/python3.13'))
    args=parser.parse_args()
    if args.device:
        from updater.bootstrap import apply
        print(json.dumps(apply(args.bundle,args.baseline)));return
    from updater.bootstrap import verify_bundle,permission_plan
    from deploy import verify_bundle as verify_root
    updater=verify_bundle(args.bundle);baseline=verify_root(args.baseline)
    plan={'operation':'one-time-root-updater-setup','replaces_root_runtime':False,'baseline':baseline['package'],
          'permissions':permission_plan(),'requires_root_mode_disabled':True,'hardware_validated':False}
    print(json.dumps(plan,indent=2))
    if not args.apply:return
    if not args.ssh:parser.error('--apply requires --ssh')
    from setup import ssh_options
    options=ssh_options(args.ssh,args.identity);remote='/tmp/cytv-root-updater-'+uuid.uuid4().hex
    subprocess.run(['ssh',*options,'umask 077; test "$(id -u)" = 0 && mkdir '+shlex.quote(remote)],check=True,stdin=subprocess.DEVNULL)
    with tempfile.TemporaryDirectory(prefix='root-updater-') as tmp:
        staging=Path(tmp)
        for kind,folder,manifest in (('updater',args.bundle,updater),('baseline',args.baseline,baseline)):
            target=staging/kind;target.mkdir()
            for name in (*manifest['files'],'bundle.json'):
                output=target/name;output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes((folder/name).read_bytes())
        subprocess.run(['scp','-O',*options[:-1],'-r',str(staging/'updater'),str(staging/'baseline'),args.ssh+':'+remote+'/'],check=True,stdin=subprocess.DEVNULL)
    argv=['env','-u','PYTHONHOME','-u','PYTHONPATH','PYTHONDONTWRITEBYTECODE=1','PYTHONNOUSERSITE=1',args.python,remote+'/updater/setup-updater.py','--device','--apply','--bundle',remote+'/updater','--baseline',remote+'/baseline']
    subprocess.run(['ssh',*options,shlex.join(argv)],check=True,stdin=subprocess.DEVNULL)


if __name__=='__main__':main()
