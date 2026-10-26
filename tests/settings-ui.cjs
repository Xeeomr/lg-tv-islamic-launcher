// Catches hidden Developer Mode actions receiving remote focus, broken Back routing,
// lost error summaries, and update markers covering their link arrows.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const base=process.env.PREVIEW_URL||'http://127.0.0.1:8876';
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'chrome'});
 try{
  for(const edition of ['launcher','root-launcher']){
   const page=await browser.newPage({viewport:{width:1920,height:1080},locale:'en'}),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   await page.goto(base+'/'+edition+'/index.html');
   await page.locator('#tiles .item').first().waitFor();
   await page.locator('#btnSettings').click();
   const panel=page.locator(edition==='launcher'?'#renewalPanel':'.root-settings:not(.root-updates)');
   const card=panel.locator('.settings-main');
   await card.waitFor({timeout:3000});
   await page.waitForFunction(()=>{const b=document.querySelector('#homeRoutingToggle')||document.querySelector('.home-routing-switch');return b&&!b.disabled;});
   assert.equal((await card.boundingBox()).width,1120);
   assert(await card.evaluate(el=>el.scrollHeight<=el.clientHeight+1),'main settings should fit without scrolling at 1080p');
   const updates=panel.locator('.settings-links button:has(.settings-update-dot)');
   await updates.evaluate(el=>el.setAttribute('data-update-available','true'));
   const marker=updates.locator('.settings-update-dot'),arrow=updates.locator('.settings-chevron');
   assert(await marker.isVisible());assert(await arrow.isVisible());
   const a=await arrow.boundingBox(),m=await marker.boundingBox();assert(m.x+m.width<a.x,'update dot must precede the trailing arrow');
   assert.equal(await marker.evaluate(el=>getComputedStyle(el).backgroundColor),'rgb(255, 179, 71)');
   await updates.evaluate(el=>el.setAttribute('data-update-available','false'));
   assert(!(await marker.isVisible()));assert(await arrow.isVisible(),'arrow remains without an update');
   if(edition==='launcher'){
    const developer=page.locator('#developerSettings');
    assert(!(await developer.isVisible()));
    await page.locator('#homeRoutingToggle').focus();
    for(let i=0;i<10;i++){
     await page.keyboard.press('ArrowRight');
     assert(await page.evaluate(()=>document.activeElement.offsetHeight>0),'remote must skip hidden actions');
    }
    await page.locator('#developerOpen').click();await developer.waitFor({state:'visible'});
    await page.keyboard.press('Escape');assert(!(await developer.isVisible()));
    assert.equal(await page.evaluate(()=>document.activeElement.id),'developerOpen');
    await page.locator('#developerOpen').click();
    await page.locator('#renewalToggle').click();
    await page.waitForFunction(()=>document.getElementById('renewalToggle').getAttribute('aria-checked')==='true');
    await page.locator('#renewalDiagnostics').click();assert(await page.locator('#renewalDetails').isVisible());
    await page.locator('#developerBack').click();
    assert(await page.locator('#renewalSummary').evaluate(el=>el.textContent.includes('enabled')));
    await updates.click();await page.locator('#updatePanel').waitFor({state:'visible'});
    await page.keyboard.press('Escape');await card.waitFor({state:'visible'});
    assert.equal(await page.evaluate(()=>document.activeElement.id),'renewalUpdates');
    await page.locator('#developerOpen').click();
    await page.evaluate(()=>{
     const call=PalmServiceBridge.prototype.call;
     PalmServiceBridge.prototype.call=function(uri,raw){
      if(uri==='luna://com.gathin.tvhome.renewal/check'){
       window.replyRenewalCheck=()=>this.onservicecallback(JSON.stringify({returnValue:true,state:{enabled:true,last:{status:'expired'},error:'setup-failed'}}));
      }else call.call(this,uri,raw);
     };
    });
    await page.locator('#renewalCheck').click();await page.locator('#developerBack').click();
    await page.evaluate(()=>window.replyRenewalCheck());
    assert.equal(await page.evaluate(()=>document.activeElement.id),'developerOpen','late renewal reply must keep focus on the visible entry');
    assert.match(await page.locator('#renewalSummary').innerText(),/setup-failed/,'setup error must remain visible outside details');
    await page.keyboard.press('Escape');await panel.waitFor({state:'hidden'});
    await page.locator('#btnSettings').click();assert(!(await developer.isVisible()),'reopening starts on main settings');
   }
   await page.waitForFunction(()=>{const b=document.querySelector('#homeRoutingToggle')||document.querySelector('.home-routing-switch');return b&&!b.disabled;});
   if(edition==='launcher')await page.waitForFunction(()=>!document.getElementById('renewalSummary').textContent.includes('Working'));
   await updates.evaluate(el=>el.setAttribute('data-update-available','true'));
   fs.mkdirSync('build/tests',{recursive:true});
   await page.screenshot({path:'build/tests/settings-'+edition+'.png'});
   for(const locale of ['en','de','es','pt-BR','fr','it','ko','hi','pl','ru']){
    await page.evaluate(code=>localStorage.setItem('tvhome.language',code),locale);
    await page.reload();await page.locator('#tiles .item').first().waitFor();await page.locator('#btnSettings').click();await card.waitFor();
    await page.evaluate(()=>document.fonts.ready);
    await updates.evaluate(el=>el.setAttribute('data-update-available','true'));
    assert(await card.evaluate(el=>el.scrollWidth<=el.clientWidth+1),locale+' horizontal overflow');
    assert(await card.evaluate(el=>el.scrollHeight<=el.clientHeight+1),locale+' main settings should fit at 1080p');
    assert(await card.locator('.settings-links button').evaluateAll(buttons=>buttons.every(el=>el.scrollWidth<=el.clientWidth+1)),locale+' link label must fit');
   }
   await page.setViewportSize({width:1280,height:720});
   assert(await card.evaluate(el=>el.scrollHeight<=el.clientHeight+1),'main settings should fit at 720p');
   assert(await card.evaluate(el=>el.scrollWidth<=el.clientWidth+1),'no horizontal overflow at 720p');
   assert.deepEqual(errors,[]);await page.close();
  }
  console.log('PASS settings layout, update indicator, Developer Mode remote/Back/error handling and ten languages in both editions');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
