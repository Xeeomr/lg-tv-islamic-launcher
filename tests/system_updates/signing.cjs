'use strict';
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const {signFeeds}=require('../../scripts/sign-release-feeds.cjs');
const policy=require('../../system-updater/policy');
const {privateKey,publicKey}=crypto.generateKeyPairSync('rsa',{modulusLength:2048});
const base='https://github.com/Razdva122/clean-your-tv-lg-webos/releases/download/v1.0.3/';
const descriptor=(name,application)=>({name,application,version:'1.0.0',kind:'ipk',url:base+application+'_1.0.0_all.ipk',sha256:'a'.repeat(64),size:12});
const set=(edition,components)=>({schema:1,release:'v1.0.3',edition,supervisor:1,notes:'Changes',components});
const manifests={
root:{schema:1,edition:'root',application:'com.cleanyourtv.root.preview',release:'v1.0.3',version:'1.0.0',runtime:1,updater:1,profile:1,url:base+'com.cleanyourtv.root.preview_1.0.0_all.ipk',sha256:'a'.repeat(64),size:12,notes:'Root'},
home:{schema:1,release:'v1.0.3',home:'1.0.1',helper:'1.0.0',url:base+'com.gathin.tvhome_1.0.1_all.ipk',sha256:'a'.repeat(64),notes:'Home'},
previous:{schema:1,release:'v1.0.3',home:'1.0.0',helper:'1.0.0',url:base+'com.gathin.tvhome_1.0.0_all.ipk',sha256:'b'.repeat(64),notes:'Prior'},
system:{'root':set('root',[descriptor('root','com.cleanyourtv.root.preview'),descriptor('root-updater','com.cleanyourtv.root.updater'),{name:'root-infrastructure',kind:'infrastructure',version:'1.0.0',url:base+'root-infrastructure_1.0.0.tar.gz',sha256:'b'.repeat(64),size:42}]),'no-root':set('no-root',[descriptor('home','com.gathin.tvhome'),{...descriptor('helper','com.local.nativehome'),url:base+'com.local.nativehome_1.0.0_arm.ipk'},descriptor('updater','com.cleanyourtv.updater')])}};
const feeds=signFeeds(manifests,privateKey,publicKey);
for(const edition of ['root','no-root'])assert.deepEqual(policy.verify(feeds['system-update-'+edition+'.json'],publicKey),manifests.system[edition]);
assert.throws(()=>signFeeds({...manifests,system:{root:manifests.system.root}},privateKey,publicKey));
console.log('PASS both edition release sets signed and verified from exact descriptors');
const {verifySystemRelease}=require('../../scripts/publish-release.cjs');
const assets={},system=JSON.parse(JSON.stringify(manifests.system));
for(const manifest of Object.values(system))for(const item of manifest.components){
 const filename=item.url.split('/').pop(),raw=Buffer.from(filename);
 item.sha256=crypto.createHash('sha256').update(raw).digest('hex');item.size=raw.length;assets[filename]=raw;
}
const exact=signFeeds({...manifests,system},privateKey,publicKey);
const build={tag:'v1.0.3',versions:{home:'1.0.0',helper:'1.0.0',updater:'1.0.0',root:'1.0.0'}};
for(const edition of ['root','no-root'])assert.equal(verifySystemRelease(exact['system-update-'+edition+'.json'],build,assets,publicKey).edition,edition);
assert.throws(()=>verifySystemRelease(exact['system-update-root.json'],{...build,versions:{...build.versions,root:'9.0.0'}},assets,publicKey),/version/);
assert.throws(()=>verifySystemRelease(exact['system-update-no-root.json'],build,{},publicKey),/package/);
console.log('PASS publication verifies both system feeds against final asset bytes and versions');
assert.throws(()=>verifySystemRelease(exact['system-update-root.json'],{...build,versions:{}},assets,publicKey),/version/);
