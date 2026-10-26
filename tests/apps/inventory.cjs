const assert=require('node:assert/strict'),fs=require('fs'),{EventEmitter}=require('events');
assert.ok(fs.existsSync(__dirname+'/../../native/service/app-inventory.js'),'TV inventory transport must exist');
const query=require('../../native/service/app-inventory');
(async()=>{
 let socket, sent=[];
 class WS extends EventEmitter {constructor(url){super();this.url=url;socket=this;queueMicrotask(()=>this.emit('open'));} send(raw){const msg=JSON.parse(raw);sent.push(msg);queueMicrotask(()=>this.emit('message',JSON.stringify(msg.type==='register'?{type:'registered'}:{id:'apps',type:'response',payload:{returnValue:true,launchPoints:[{id:'a',title:'Alpha'}]}})));} terminate(){this.closed=true;}}
 const options={WebSocket:WS,readKey:()=>({key:'paired'}),interfaces:()=>({eth0:[{internal:false,family:'IPv4',address:'192.168.1.5'}]}),timeout:100};
 assert.deepEqual(await query(options),[{id:'a',title:'Alpha'}]);assert(socket.closed);assert.equal(socket.url,'wss://192.168.1.5:3001');
 assert.equal(sent[1].uri,'ssap://com.webos.applicationManager/listLaunchPoints');
 await assert.rejects(query({...options,readKey:()=>({})}),/pairing/);
 await assert.rejects(query({...options,interfaces:()=>({})}),/network/);
 class Multi extends WS {send(raw){if(this.url.includes('192.168.1.6'))super.send(raw);else queueMicrotask(()=>this.emit('error',Error('offline')));}}
 assert.deepEqual(await query({...options,WebSocket:Multi,interfaces:()=>({eth0:[{internal:false,family:'IPv4',address:'192.168.1.5'},{internal:false,family:'IPv4',address:'192.168.1.6'}]})}),[{id:'a',title:'Alpha'}]);
 class Revoked extends WS {send(){queueMicrotask(()=>this.emit('message',JSON.stringify({payload:{pairingType:'PROMPT'}})));}}
 await assert.rejects(query({...options,WebSocket:Revoked}),/pairing/);assert(socket.closed);
 class Silent extends WS {send(){}}
 await assert.rejects(query({...options,WebSocket:Silent}),/timeout/);assert(socket.closed);
 const root=require('../../root-edition/service/app-inventory');
 const calls=[];
 const apps=await root((file,args,opts,cb)=>{calls.push({file,args});cb(null,JSON.stringify({returnValue:true,apps:[{id:'a',title:'Alpha',icon:'a.png',folderPath:'/tmp/untrusted'}]}));},()=>0);
 assert.equal(apps[0].id,'a');assert.equal(apps[0].icon,'');assert.equal(calls[0].args[2],'luna://com.webos.applicationManager/dev/listApps');
 await assert.rejects(root(()=>{throw Error('should not run')},()=>1000),/Root/);
 console.log('PASS TV inventory, local endpoint, missing/revoked pairing, timeout, root listing');
})().catch(e=>{console.error(e);process.exitCode=1;});
