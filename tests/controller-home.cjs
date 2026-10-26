const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict'),EventEmitter=require('events');
let now=1000,worker,watch,start,tick;const methods={},calls=[],commands=[],files=new Map();
function Service(){this.register=(n,f)=>methods[n]=f;this.activityManager={create(){}};this.call=(uri,p,cb)=>{if(uri.endsWith('/launch'))calls.push(p.id);cb({payload:{returnValue:true,state:{enabled:true,schema:3}}});};}
const fakefs={existsSync:()=>false,writeFileSync:(p,s)=>files.set(p,s),renameSync:(a,b)=>{files.set(b,files.get(a));files.delete(a);},chmodSync(){},unlinkSync(){},appendFileSync(){},readFileSync(p){if(p.endsWith('apps.json'))return '["test.app"]';if(files.has(p))return files.get(p);const e=new Error('missing');e.code='ENOENT';throw e;}};
const context={Buffer,require(n){if(n==='./state-permissions')return()=>true;if(n==='fs')return fakefs;if(n==='child_process')return{spawn(){worker=new EventEmitter();worker.stdout=new EventEmitter();worker.stderr=new EventEmitter();worker.stdin=new EventEmitter();worker.stdin.write=c=>commands.push(c);worker.stdin.end=()=>{throw Error('worker must stay active')};return worker;}};if(n==='/usr/lib/node_modules/webos-service')return Service;if(n==='./screen-watch')return(d,l,fg,reset,power)=>{watch={fg,power};return{close(){}}};return require('../native/app/'+n.slice(2));},process:{argv:['node','app','{"nativeHomeAuto":true}'],pid:1,getuid:()=>5431,hrtime:()=>[Math.floor(now/1000),(now%1000)*1e6],on(){},exit(){throw Error('must not stop')}},setTimeout(fn,ms){if(ms===0)start=fn;return 1;},clearTimeout(){},setInterval(fn){tick=fn;},clearInterval(){}};
vm.runInNewContext(fs.readFileSync('native/app/native.js','utf8'),context);start();worker.stdout.emit('data',Buffer.from('READY\n'));
let seq=0;function rpc(n,p={}){files.set('/media/developer/apps/usr/palm/applications/com.local.nativehome/state/home-request.json',JSON.stringify({id:(++seq).toString(16).padStart(32,'0'),method:n,enabled:p.enabled,expires:Date.now()+5000}));tick();return JSON.parse(files.get('/media/developer/apps/usr/palm/applications/com.local.nativehome/state/home-response.json'));}
assert.equal(rpc('homeStatus').enabled,true);
// Installing the separate Home app closes its UI. That foreground transition
// must leave the detached helper/relay alive without trying to reopen the app
// while SAM may still be replacing it.
watch.fg('com.gathin.tvhome');const beforeUpdateClose=calls.length;
watch.fg('');watch.fg('com.webos.app.home');
assert.equal(calls.length,beforeUpdateClose,'Home closure must not trigger a helper launch attempt');
assert.equal(rpc('homeStatus').enabled,true,'Home closure must preserve routing');
assert.equal(files.get('/media/developer/apps/usr/palm/applications/com.local.nativehome/state/controller.pid'),'1');
assert(!commands.includes('Q'),'Home closure must not stop the relay');
watch.fg('test.app');worker.stdout.emit('data',Buffer.from('LGHOME\n'));assert.equal(calls.at(-1),'com.webos.app.home');
const count=calls.length;watch.fg('com.webos.app.home');assert.equal(calls.length,count,'explicit visit must not bounce back');assert.equal(rpc('homeStatus').enabled,true);
worker.stdout.emit('data',Buffer.from('HOME\n'));assert.equal(calls.at(-1),'com.gathin.tvhome');
assert.equal(rpc('setHomeControl',{enabled:false}).enabled,false);assert.equal(commands.filter(c=>c!=='P').at(-1),'D');
let before=calls.length;watch.fg('test.app');watch.fg('com.webos.app.home');worker.stdout.emit('data',Buffer.from('HOME\n'));assert.equal(calls.length,before);
rpc('openLGHome');assert.equal(rpc('homeStatus').enabled,false);assert.equal(calls.at(-1),'com.webos.app.home');
rpc('setHomeControl',{enabled:true});assert.equal(commands.filter(c=>c!=='P').at(-1),'E');now+=8000;worker.stdout.emit('data',Buffer.from('P\n'));before=calls.length;watch.fg('test.app');watch.fg('com.webos.app.home');assert.equal(calls.length,before+1);
assert(![...files.keys()].some(p=>p.endsWith('/blocked')));assert.equal(rpc('setHomeControl',{enabled:'false'}).returnValue,false);
console.log('PASS real controller: one-time LG visit, next Home, disabled Home/Back routing, persisted preference, no emergency latch');
