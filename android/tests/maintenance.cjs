const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const vm = require('node:vm');
const ui = path.resolve(__dirname, '../app/src/main/assets/ui');
const {words} = vm.runInNewContext(fs.readFileSync(path.join(ui, 'translations.js'), 'utf8') + ';({words})');
let browser;
(async () => {
  browser = await chromium.launch({headless:true, executablePath:process.env.CYTV_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  for (const [locale, dictionary] of Object.entries(words)) {
    for (const action of ['status', 'restore', 'home-diagnostics']) {
      const page = await browser.newPage({locale, viewport:{width:320, height:740}, reducedMotion:'reduce'});
      await page.addInitScript(() => {
        window.requests = [];
        window.CYTV = {
          hasKey:()=>false, snapshot:()=> '[]', answer:()=>{}, saveReport:()=>requests.push({saveReport:true}),
          inspect:config=>receiveNative({kind:'inspection', host:JSON.parse(config).host, root_ssh:true, developer_ssh:false}),
          start:config=>requests.push(JSON.parse(config)),
        };
      });
      await page.goto('file://' + path.join(ui, 'index.html'));
      await page.locator('[data-action=tools]').click();
      assert.equal(await page.locator('.steps').count(), 0);
      await page.locator(`[data-action=choose-${action==='home-diagnostics'?'diagnostics':action}]`).click();
      assert.equal(await page.locator('h1').innerText(), dictionary[action==='home-diagnostics'?'homeDiagnostics':action==='status'?'statusTool':'restore']);
      await page.locator('#host').fill('192.168.1.50');
      await page.locator('[data-action=inspect]').click();
      assert.equal(await page.locator('.steps').count(), 0);
      assert.equal(await page.locator('h1').innerText(), dictionary.connectionMethod);
      await page.locator('[data-action=back]').click();
      assert.equal(await page.locator('h1').innerText(), dictionary[action==='home-diagnostics'?'homeDiagnostics':action==='status'?'statusTool':'restore']);
      assert.equal(await page.locator('#host').inputValue(), '192.168.1.50');
      await page.locator('[data-action=inspect]').click();
      await page.locator('[data-action=connect]').click();
      assert.equal(await page.locator('h1').innerText(), dictionary[action==='home-diagnostics'?'homeDiagnostics':action==='status'?'statusTool':'restore']);
      assert(!(await page.locator('body').innerText()).includes(dictionary.reviewFoot));
      await page.locator('[data-action=start]').click();
      assert.equal(await page.evaluate(()=>requests.at(-1).action), action);
      assert.equal(await page.locator('.task-list').count(), 0);
      assert.equal(await page.locator('.progress-copy p').innerText(), dictionary[action==='home-diagnostics'?'diagnosticProgress':'maintenanceProgress']);
      assert.equal(await page.locator('#live-caption').innerText(), dictionary.awaiting);
      const expectedTitle = dictionary[action==='home-diagnostics'?'homeDiagnostics':action==='status'?'statusTitle':'restoreTitle'].replace('<br>', '\n');
      assert.equal(await page.locator('[role=progressbar]').getAttribute('aria-label'), expectedTitle.replace('\n', ' '));
      await page.evaluate(()=>receiveNative({kind:'stage', stage:3}));
      assert.equal(await page.locator('.task-list').count(), 0);
      // Activity recreation replays the action, rather than installation defaults.
      await page.evaluate(a=>receiveNative({kind:'started', config:{host:'192.168.1.50', edition:'root', action:a}}), action);
      assert.equal(await page.locator('.task-list').count(), 0);
      const typography = await page.locator('.progress-copy p').evaluate(el=>({size:parseFloat(getComputedStyle(el).fontSize), family:getComputedStyle(el).fontFamily}));
      assert(typography.size >= 16);
      assert(typography.family.startsWith('system-ui'));
      for (const [width,height] of [[320,740],[375,667],[740,375]]) {
        await page.setViewportSize({width,height});
        assert(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth), `${locale}/${action}/${width} overflow`);
      }
      if(action==='home-diagnostics'){
        await page.evaluate(()=>{receiveNative({kind:'report-ready',name:'diagnostic-123456abcdef.json'});receiveNative({kind:'finished',code:0});});
        await page.locator('[data-action=save-report]').click();
        assert.equal(await page.evaluate(()=>requests.at(-1).saveReport),true);
        assert.equal(await page.locator('h1').innerText(),dictionary.reportDone);
      }
      await page.close();
    }
  }
  await browser.close();
  console.log('PASS Android maintenance: ten locales, correct commands, connection flow, progress, replay, readable text and responsive widths');
})().catch(async error=>{console.error(error);if(browser)await browser.close();process.exitCode=1});
