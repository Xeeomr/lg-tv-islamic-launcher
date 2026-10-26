// Real kernel ownership/permission enforcement, run with sudo on Linux CI.
const a=require('node:assert/strict'),fs=require('fs'),os=require('os'),path=require('path'),cp=require('child_process');
if(process.platform!=='linux'||process.getuid()!==0){
 console.log('SKIP: real multi-UID permissions require Linux root (covered by CI)');
}else{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'cytv-uids-')),state=path.join(root,'state'),key=path.join(state,'ssap-key.json');
 const modulePath=require.resolve('../app/state-permissions');
 // Copy the runtime to a traversable temporary directory, independent of checkout permissions.
 fs.copyFileSync(modulePath,path.join(root,'state-permissions.js'));fs.chmodSync(root,0o755);
 function run(uid,script){
  const result=cp.spawnSync(process.execPath,['-e',
   'process.setgroups([5000]);process.setgid(5000);process.setuid('+uid+');'+script],{encoding:'utf8'});
  a.equal(result.status,0,result.stderr||result.stdout);
 }
 const check='if(!require('+JSON.stringify(path.join(root,'state-permissions.js'))+')('+JSON.stringify(state)+'))process.exit(1);';
 try{
  fs.mkdirSync(state);fs.chownSync(state,5999,5000);fs.chmodSync(state,0o775);
  fs.writeFileSync(key,'{"key":"test-key"}');fs.chownSync(key,5580,5000);fs.chmodSync(key,0o775);
  fs.writeFileSync(path.join(state,'apps.json'),'["test.app"]');fs.chownSync(path.join(state,'apps.json'),5580,5000);fs.chmodSync(path.join(state,'apps.json'),0o775);
  run(5367,check);
  a.equal(fs.statSync(key).uid,5367);a.equal(fs.statSync(key).gid,5000);a.equal(fs.statSync(key).mode&0o777,0o640);
  run(5380,check+'if(JSON.parse(require("fs").readFileSync('+JSON.stringify(key)+')).key!=="test-key")process.exit(2);');
  // Developer Mode setup can still atomically upload a new key after repair.
  run(5580,'var fs=require("fs"),p='+JSON.stringify(key)+';fs.writeFileSync(p+".new",\'{"key":"updated-key"}\',{mode:0o640});fs.renameSync(p+".new",p);');
  run(5367,check);a.equal(JSON.parse(fs.readFileSync(key)).key,'updated-key');
  fs.chmodSync(key,0o775);fs.chmodSync(state,0o755);
  run(5367,'if(require('+JSON.stringify(path.join(root,'state-permissions.js'))+')('+JSON.stringify(state)+'))process.exit(3);');
  a.equal(fs.statSync(key).mode&0o777,0o775);
  console.log('PASS: real installer/developer/helper/service UIDs, shared group, reconfiguration, denied replacement');
 }finally{fs.rmSync(root,{recursive:true,force:true});}
}
