'use strict';
// Real Chromium is required: insertText's paragraph behaviour is the regression.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const source = fs.readFileSync(path.join(__dirname, '../web/app.js'), 'utf8');
const helpers = source.slice(source.indexOf('function el('), source.indexOf('/* ---------------- drawn glyphs'));
const editor = source.slice(source.indexOf('function renderRadiologyTemplate('), source.indexOf('function renderQuickReport('));
const targetStart = source.indexOf('  let workingEditor;', source.indexOf('const templates = legacy.querySelector'));
const tracking = source.slice(targetStart, source.indexOf('  const choices = [', targetStart));
const promptsStart = source.indexOf('      usePrompts: system => {') + '      usePrompts: system => {'.length;
const prompts = source.slice(promptsStart, source.indexOf('\n      },\n    }))]]', promptsStart));
assert.ok(targetStart > 0 && promptsStart > 0 && tracking.includes('currentReportEditor'));
const text = 'Clinical history:\r\nSynthetic report: 6.00 × 4.50 mm < 8 mm; a & b.\r\n\r\nComparison:\r\n2025-03-04 (synthetic prior).\r\n\r\nImpression:\r\n1. Keep the clinician’s “indeterminate” wording.';
const normalised = text.replace(/\r\n?/g, '\n');
(async () => {
  const browser = await chromium.launch({headless: true, ...(process.env.CHROMIUM_PATH ? {executablePath: process.env.CHROMIUM_PATH} : {})});
  try {
    for (const width of [1440, 390]) {
      const page = await browser.newPage({viewport: {width, height: 1000}});
      await page.route('http://127.0.0.1:8793/**', route => route.fulfill({status:200,contentType:'text/html',body:'<main></main>'}));
      await page.goto('http://127.0.0.1:8793/');
      await page.addStyleTag({path: path.join(__dirname, '../web/radiology-structured.css')});
      await page.addScriptTag({path: path.join(__dirname, '../web/radiology-structured.js')});
      await page.addScriptTag({content: `${helpers}\n${editor}\nfunction track(templates) { ${tracking} return currentReportEditor; }\nfunction appendPrompts(system) { ${prompts} }\nconst choices=[['template']]; function activate() { window.activated=true; }`});
      await page.evaluate(() => {
        const templates = document.createElement('div'); document.querySelector('main').append(templates);
        for (const [i, title] of ['Dictation template', 'Fast template', 'Normal report'].entries()) templates.append(renderRadiologyTemplate({title, text:'Clinical history:\n[]\n\nComparison:\n[]\n\nStudy\nFindings:\n[]\n\nImpression:\n[]'},i,'fixture',true));
        window.currentReportEditor = track(templates);
        window.system = {title:'Named source standard',version:'test edition',report_fields:['Extent','Nodes']};
        Object.defineProperty(navigator,'clipboard',{configurable:true,value:{write:async items=>{const output={};for(const item of items)for(const type of item.types)output[type]=await(await item.getType(type)).text();window.copied=output;}}});
      });
      const drafts=page.locator('.rad-template'), first=drafts.nth(0).locator('[contenteditable]'), fast=drafts.nth(1).locator('[contenteditable]');
      const original=await first.innerHTML();
      await fast.fill('Before paste sentinel.');await fast.focus();
      await fast.evaluate((node,text)=>{const range=document.createRange();range.selectNodeContents(node);getSelection().removeAllRanges();getSelection().addRange(range);const data=new DataTransfer();data.setData('text/plain',text);data.setData('text/html','<img src="invalid" onerror="window.untrusted=true"><b>Wrong rich paste</b>');node.dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}));},text);
      assert.equal(await fast.innerText(),normalised,'one authored blank line stays one blank line');
      assert.equal(await fast.locator('img,b,[style]').count(),0,'clipboard HTML is never inserted');
      await fast.evaluate(()=>document.execCommand('undo'));assert.equal(await fast.innerText(),'Before paste sentinel.','one native undo reverses the whole paste');
      await fast.evaluate(()=>document.execCommand('redo'));assert.equal(await fast.innerText(),normalised);
      const prefix=await fast.innerHTML();await page.evaluate(()=>appendPrompts(system));
      assert.equal(await first.innerHTML(),original,'unrelated first draft is untouched');
      assert.ok((await fast.innerHTML()).startsWith(prefix),'the working draft DOM is retained');
      assert.equal(await fast.locator('u').filter({hasText:'STAGING REVIEW — Named source standard (test edition)'}).count(),1);
      assert.equal(await fast.locator('em').filter({hasText:'Extent:'}).count(),1);
      assert.equal(await fast.locator('em').filter({hasText:'Extent:'}).evaluate(e=>e.nextElementSibling.textContent),' [].');
      assert.deepEqual(await fast.locator('em').filter({hasText:'Extent:'}).evaluate(e=>[getComputedStyle(e).fontStyle,getComputedStyle(e.nextElementSibling).fontStyle]),['italic','normal']);
      assert.equal(await fast.evaluate(e=>getComputedStyle(e).fontSize),'16px');
      assert.ok(await drafts.nth(1).getByRole('button',{name:'Reset edits',exact:true}).isEnabled());
      await drafts.nth(1).getByRole('button',{name:'Copy text',exact:true}).click();await page.waitForFunction(()=>!!window.copied?.['text/plain']);
      const copied=await page.evaluate(()=>window.copied);assert.ok(copied['text/plain'].startsWith(normalised));assert.ok(copied['text/html'].includes('font-size:12pt'));assert.ok(copied['text/html'].includes('&lt; 8 mm; a &amp; b.'));
      const saved=await fast.innerHTML();await drafts.nth(2).locator('[contenteditable]').focus();await page.evaluate(()=>appendPrompts(system));assert.equal(await fast.innerHTML(),saved,'switching to another draft keeps the previous report');
      assert.ok((await drafts.nth(2).locator('[contenteditable]').innerText()).includes('STAGING REVIEW'));
      assert.ok(await page.evaluate(()=>!window.untrusted));
      console.log(width+' report paste: paragraph spacing, escaped text, exact measurements, native undo/redo, active draft, unchanged other drafts, heading styles and both clipboard formats passed');
      await page.close();
    }
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
