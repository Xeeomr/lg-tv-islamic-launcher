#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const rootPolicy=require('../root-edition/updater/fetch'),homePolicy=require('../updater-service/policy'),systemPolicy=require('../system-updater/policy');
function signFeeds(manifests,privateKey,publicKey=fs.readFileSync(path.join(__dirname,'../updater-service/release-public.pem'))){
 function sign(manifest,policy){
  const bytes=Buffer.from(JSON.stringify(manifest,null,2)+'\n');
  const envelope={payload:bytes.toString('base64'),signature:crypto.sign('RSA-SHA256',bytes,privateKey).toString('base64')};
  policy.verify(envelope,publicKey);return envelope;
 }
 const root=sign(manifests.root,rootPolicy),home=sign(manifests.home,homePolicy),previous=sign(manifests.previous,homePolicy);
 if(manifests.previous.helper!==manifests.home.helper||homePolicy.compare(manifests.previous.home,manifests.home.home)>=0)throw Error('incompatible-home-rollback');
 const result={'root-update.json':root,'update.json':{...home,previous},'previous-update.json':previous};
 if(manifests.system){for(const edition of ['root','no-root']){
  if(!manifests.system[edition]||manifests.system[edition].edition!==edition||manifests.system[edition].release!==manifests.root.release)throw Error('system-release-set-required');
  result['system-update-'+edition+'.json']=sign(manifests.system[edition],systemPolicy);
 }}
 return result;
}
module.exports={signFeeds};
if(require.main===module){
 try{
  const [input,output]=process.argv.slice(2);
  if(!input||!output||!process.env.UPDATE_SIGNING_PRIVATE_KEY)throw Error('Manifest paths and UPDATE_SIGNING_PRIVATE_KEY are required');
  const key=process.env.UPDATE_SIGNING_PRIVATE_KEY;delete process.env.UPDATE_SIGNING_PRIVATE_KEY;
  const feeds=signFeeds(JSON.parse(fs.readFileSync(input)),key);
  fs.mkdirSync(output,{recursive:true});
  for(const [name,feed] of Object.entries(feeds))fs.writeFileSync(path.join(output,name),JSON.stringify(feed,null,2)+'\n',{flag:'wx'});
  process.stdout.write('Signed and verified Root, Home, rollback and system release feeds with the pinned release key.\n');
 }catch(error){process.stderr.write(error.message+'\n');process.exitCode=1;}
}
