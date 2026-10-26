const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ui = path.resolve(__dirname, '../app/src/main/assets/ui');
const {words, languages} = vm.runInNewContext(fs.readFileSync(path.join(ui, 'translations.js'), 'utf8') + ';({words,languages})');
const expected = ['de','en','es','fr','hi','it','ko','pl','pt-BR','ru'];
assert.deepEqual(Object.keys(languages).sort(), expected);
assert.deepEqual(Object.keys(words).sort(), expected);
for (const [code, dictionary] of Object.entries(words)) {
  assert.deepEqual(Object.keys(dictionary).sort(), Object.keys(words.en).sort(), code);
  for (const [key, value] of Object.entries(dictionary)) {
    assert.equal(Array.isArray(value), Array.isArray(words.en[key]), `${code}.${key}`);
    for (const text of [].concat(value)) {
      assert.equal(typeof text, 'string'); assert(text.trim(), `${code}.${key}`);
      assert(!/<(?!br\s*\/?>)[^>]*>/i.test(text), `Unexpected markup in ${code}.${key}`);
    }
  }
}
let browser;
(async () => {
  browser = await chromium.launch({headless:true, executablePath:process.env.CYTV_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const page = await browser.newPage({viewport:{width:320,height:740}, locale:'ru-RU'});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(() => {
    window.requests=[];
    window.CYTV={hasKey:()=>false,snapshot:()=> '[]',inspect:c=>receiveNative({kind:'inspection',host:JSON.parse(c).host,root_ssh:true,developer_ssh:false}),start:c=>requests.push(JSON.parse(c)),answer:()=>{}};
  });
  const url='file://' + path.join(ui, 'index.html');
  await page.goto(url);
  assert.equal(await page.locator('.language').textContent(), 'RU');
  await page.locator('#host').fill('192.168.1.50');
  for (const code of expected) {
    await page.locator('.language').click();
    assert.equal(await page.locator('#language-picker [role=radio]').count(), 10);
    await page.locator(`[data-language="${code}"]`).click();
    assert.equal(await page.locator('html').getAttribute('lang'), code);
    assert.equal(await page.locator('.language').textContent(), code.toUpperCase());
    assert.equal(await page.locator('#host').inputValue(), '192.168.1.50');
    assert.equal(await page.locator('h1').innerText(), words[code].hero.replace('<br>', '\n'));
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth), true, `${code} welcome overflow`);
    await page.reload();
    assert.equal(await page.locator('html').getAttribute('lang'), code);
    await page.locator('#host').fill('192.168.1.50');
  }
  await page.locator('[data-action=inspect]').click();
  await page.locator('[data-action=connect]').click();
  await page.locator('#port').fill('2222');
  await page.locator('.language').click();
  await page.locator('[data-language=de]').click();
  assert.equal(await page.locator('#port').inputValue(), '2222');
  await page.locator('[data-action=start]').click();
  assert.equal(await page.evaluate(()=>requests[0].language), 'de');
  await page.evaluate(()=>receiveNative({kind:'secret',id:'secret',secretType:'key',text:'SSH key passphrase:'}));
  assert.equal(await page.locator('#prompt-title').textContent(), words.de.keySecretTitle);
  await page.locator('#prompt-value').fill('SENSITIVE');
  await page.keyboard.press('Escape');
  assert(!(await page.locator('body').innerText()).includes('SENSITIVE'));
  await page.evaluate(()=>receiveNative({kind:'stage',stage:3}));
  assert.equal(await page.locator('.task-list li.complete').count(), 3);
  await page.evaluate(()=>receiveNative({kind:'finished',code:0}));
  await page.locator('[data-action=home]').click();
  await page.locator('[data-action=tools]').click();
  await page.locator('[data-action=choose-restore]').click();
  await page.locator('[data-action=start]').click();
  assert.equal(await page.evaluate(()=>requests.at(-1).action), 'restore');
  await page.evaluate(()=>receiveNative({kind:'finished',code:0}));
  await page.locator('[data-action=home]').click();
  await page.locator('[data-action=inspect]').click();
  await page.locator('[data-action=connect]').click();
  await page.locator('[data-action=start]').click();
  assert.equal(await page.evaluate(()=>requests.at(-1).action), 'install');
  assert.deepEqual(errors, []);
  await page.close();
  for (const [locale, saved, selected] of [['pt-PT',null,'pt-BR'],['ko-KR','invalid','ko'],['ja-JP',null,'en']]) {
    const context=await browser.newContext({locale});
    const p=await context.newPage();
    if(saved) await p.addInitScript(value=>localStorage.setItem('cytv-language',value),saved);
    await p.goto(url);
    assert.equal(await p.locator('html').getAttribute('lang'),selected);
    await context.close();
  }
  for (const code of expected) {
    const context=await browser.newContext({locale:code,viewport:{width:320,height:740}});
    const p=await context.newPage();
    p.on('pageerror', error=>errors.push(error.message));
    for (const mode of ['welcome','editions','connect','root','progress','success']) {
      await p.goto(url+'?preview='+mode);
      await p.evaluate(()=>document.fonts.ready);
      assert.equal(await p.locator('html').getAttribute('lang'),code);
      assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth <= innerWidth),true,`${code}/${mode} overflow`);
      assert(!(await p.locator('body').innerText()).includes('undefined'),`${code}/${mode} missing text`);
    }
    await context.close();
  }
  assert.deepEqual(errors, []);
  await browser.close();
  console.log('All ten Android locales: complete catalogs, current-language picker, persistence, system locale, form preservation and localized native requests passed.');
})().catch(async error=>{console.error(error);if(browser)await browser.close();process.exitCode=1});
