const assert=require('node:assert/strict'),fs=require('fs'),os=require('os'),path=require('path');
const create=require('../renewal-service/home-control');
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'cytv-control-'));
(async()=>{try{
 let now=0,queue=[],seq=0;const send=create(fs,dir,{now:()=>now,later:f=>queue.push(f),nonce:()=>String(++seq).padStart(32,'0')});
 fs.writeFileSync(path.join(dir,'home-response.json'),JSON.stringify({id:'old',returnValue:true,enabled:false}));
 let pending=send('setHomeControl',{enabled:false});let req=JSON.parse(fs.readFileSync(path.join(dir,'home-request.json'),'utf8'));
 assert.equal(req.enabled,false);assert.equal(req.method,'setHomeControl');assert.equal((await send('openLGHome',{})).returnValue,false,'serialize commands');
 fs.writeFileSync(path.join(dir,'home-response.json'),JSON.stringify({id:req.id,returnValue:true,enabled:false}));queue.shift()();assert.equal((await pending).enabled,false);
 pending=send('openLGHome',{});now=5001;queue.shift()();assert.equal((await pending).returnValue,false,'stale responses cannot confirm a new command');
 assert.equal((await send('setHomeControl',{enabled:'false'})).returnValue,false);
 assert.equal((await send('shell',{command:'noop'})).returnValue,false);
 console.log('PASS same-package Home broker: fixed commands, serialization, correlated response, timeout and validation');
}finally{fs.rmSync(dir,{recursive:true});}})().catch(e=>{console.error(e);process.exitCode=1;});
