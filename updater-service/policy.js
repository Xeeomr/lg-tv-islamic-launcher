'use strict';
var crypto=require('crypto');
var REPO='https://github.com/Razdva122/clean-your-tv-lg-webos/releases/download/';
function version(v){if(typeof v!=='string'||!/^\d{1,4}\.\d{1,4}\.\d{1,4}$/.test(v))throw Error('invalid-version');return v.split('.').map(Number);}
function compare(a,b){a=version(a);b=version(b);for(var i=0;i<3;i++)if(a[i]!==b[i])return a[i]>b[i]?1:-1;return 0;}
function verify(e,key){
 if(!e||typeof e.payload!=='string'||typeof e.signature!=='string'||e.payload.length>32768||e.signature.length>2048)throw Error('invalid-envelope');
 var bytes=Buffer.from(e.payload,'base64');
 if(bytes.toString('base64')!==e.payload)throw Error('invalid-envelope');
 var verifier=crypto.createVerify('RSA-SHA256');verifier.update(bytes);verifier.end();
 if(!verifier.verify(key,e.signature,'base64'))throw Error('invalid-signature');
 var m=JSON.parse(bytes.toString('utf8'));version(m.home);version(m.helper);
 if(m.schema!==1||!/^v\d{1,4}\.\d{1,4}\.\d{1,4}$/.test(m.release)||!/^([a-f0-9]{64})$/.test(m.sha256)||
 m.url!==REPO+m.release+'/com.gathin.tvhome_'+m.home+'_all.ipk'||typeof m.notes!=='string'||m.notes.length>4000)throw Error('invalid-manifest');
 return {schema:1,release:m.release,home:m.home,helper:m.helper,url:m.url,sha256:m.sha256,notes:m.notes};
}
function offer(m,home,helper){var c=compare(m.home,home);if(c===0)return 'current';if(c<0)return 'newer-installed';return helper===m.helper?'available':'helper-update-required';}
module.exports={verify:verify,offer:offer,compare:compare};
