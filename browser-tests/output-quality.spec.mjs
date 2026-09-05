import {test,expect} from '@playwright/test';
import {execFileSync} from 'node:child_process';
import {mkdtempSync,readFileSync,writeFileSync,rmSync,existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const python=existsSync(path.join(root,'.venv/bin/python'))?path.join(root,'.venv/bin/python'):'python3';
const renderer=path.join(root,'skills/agentic-aac-board-maker/scripts/render_html.py');
const source=path.join(root,'generated/gaze-choice-2x2/gaze-choice-class-activity.ir.json');
let scratch;
test.beforeAll(()=>{scratch=mkdtempSync(path.join(tmpdir(),'aac-output-'));});
test.afterAll(()=>rmSync(scratch,{recursive:true,force:true}));
function renderCandidate(edit){const ir=JSON.parse(readFileSync(source));edit(ir);const input=path.join(scratch,'candidate.ir.json'),output=path.join(scratch,'candidate.html');writeFileSync(input,JSON.stringify(ir));execFileSync(python,[renderer,input,output]);return output;}
async function open(page,file){await page.addInitScript(()=>{window.__spoken=[];window.SpeechSynthesisUtterance=class {constructor(text){this.text=text;}};Object.defineProperty(window,'speechSynthesis',{value:{cancel(){},speak(utterance){window.__spoken.push(utterance.text);window.__utterance=utterance;utterance.onstart?.();}}});});await page.goto(pathToFileURL(file).href);}

test('touch-only start, vocabulary and stop work with keyboard',async({page})=>{
 const file=renderCandidate(ir=>{ir.access.profile='touch';ir.access.intended=['touch','keyboard'];ir.access.dwellTimeMs=null;});
 await open(page,file);await page.getByRole('button',{name:'Start board'}).focus();await page.keyboard.press('Enter');
 await expect(page.locator('#student-layer')).toBeVisible();await page.locator('#btn-art').focus();await page.keyboard.press('Space');
 expect(await page.evaluate(()=>window.__spoken)).toEqual(['Art']);
 await expect(page.locator('#stop-speech')).toBeFocused();await page.keyboard.press('Enter');
 await expect(page.locator('#btn-art')).toBeFocused();await expect(page.locator('#selected-message')).toHaveText('Art');
 await page.locator('#btn-art').click();expect(await page.evaluate(()=>window.__spoken.length)).toBe(2);
});

test('speech completion and error restore visible focus',async({page})=>{
 await open(page,path.join(root,'generated/gaze-choice-2x2/gaze-choice-class-activity.html'));await page.locator('#start').click();
 for(const callback of ['onend','onerror']){await page.locator('#btn-art').click();await page.evaluate(c=>window.__utterance[c](),callback);await expect(page.locator('#btn-art')).toBeFocused();}
});

test('speech unavailable retains readable selected message',async({page})=>{
 await open(page,path.join(root,'generated/gaze-choice-2x2/gaze-choice-class-activity.html'));await page.evaluate(()=>{window.SpeechSynthesisUtterance=undefined;});await page.locator('#start').click();await page.locator('#btn-art').click();await expect(page.locator('#selected-message')).toBeVisible();await expect(page.locator('#selected-message')).toHaveText('Art');
});

test('explicit slots preserve positions and keyboard order',async({page})=>{
 const file=renderCandidate(ir=>{[ir.pages[0].buttons[0].position,ir.pages[0].buttons[1].position]=[ir.pages[0].buttons[1].position,ir.pages[0].buttons[0].position];ir.pages[0].buttons[1].font={size:32,colour:'#123456'};});
 await open(page,file);await page.locator('#start').click();await expect(page.locator('#btn-art')).toBeFocused();
 const a=await page.locator('#btn-art').boundingBox(),b=await page.locator('#btn-read').boundingBox();expect(a.x).toBeLessThan(b.x);await expect(page.locator('#btn-art')).toHaveCSS('font-size','32px');await page.keyboard.press('Tab');await expect(page.locator('#btn-read')).toBeFocused();
});

test('embedded symbols decode offline and print scan numbers are visible',async({page})=>{
 await page.context().setOffline(true);await open(page,path.join(root,'generated/symbol-shape-choice/symbol-shape-choice.html'));await page.locator('#start').click();
 const images=page.locator('.symbol');await expect(images).toHaveCount(6);expect(await images.evaluateAll(items=>items.every(img=>img.complete&&img.naturalWidth>0))).toBe(true);
 await page.emulateMedia({media:'print'});await expect(page.locator('.scan-number').first()).toBeVisible();expect(await page.locator('.scan-number').allTextContents()).toEqual(['1. ','2. ','3. ','4. ','5. ','6. ']);
});

test('hero example constructs a complete opinion and reason',async({page})=>{
 await open(page,path.join(root,'generated/curriculum-sentence-builder/year7-hero-speech-sentence-builder.html'));await page.locator('#start').click();
 for(const label of ['My hero is…','a firefighter','I think…']){await page.getByRole('button',{name:label,exact:true}).click();await page.evaluate(()=>window.__utterance.onend());}
 await page.getByRole('button',{name:'Describing words ▶',exact:true}).click();await page.getByRole('button',{name:'brave',exact:true}).click();await page.evaluate(()=>window.__utterance.onend());
 await page.getByRole('button',{name:'◀ Sentence starters',exact:true}).click();await page.getByRole('button',{name:'because',exact:true}).click();await page.evaluate(()=>window.__utterance.onend());
 await page.getByRole('button',{name:'Describing words ▶',exact:true}).click();await page.getByRole('button',{name:'helps others',exact:true}).click();await page.evaluate(()=>window.__utterance.onend());
 await expect(page.locator('#message-text')).toHaveText('My hero is a firefighter. I think they are brave because they help others.');
});

test('long labels remain inside targets at a small classroom viewport',async({page})=>{
 const file=renderCandidate(ir=>{ir.pages[0].buttons[0].label='I would like to choose something different';});
 await page.setViewportSize({width:1024,height:600});await open(page,file);await page.locator('#start').click();
 expect(await page.locator('#btn-read').evaluate(button=>{const b=button.getBoundingClientRect(),t=button.querySelector('.label').getBoundingClientRect();return t.left>=b.left&&t.right<=b.right&&t.top>=b.top&&t.bottom<=b.bottom;})).toBe(true);
});

test('offline symbol review downloads chosen decisions',async({page})=>{
 const review=path.join(scratch,'review.html');
 execFileSync(python,['-c',`import sys,json;sys.path.insert(0,sys.argv[1]);from fetch_arasaac_symbols import render_review_html;from pathlib import Path;m={'boardFingerprint':'test-revision','entries':[{'label':'Circle','pageId':'p','buttonId':'b','candidates':[{'symbolId':1,'imageData':'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg"/%3E','score':1,'keywords':['circle']},{'symbolId':2,'imageData':'','score':0,'keywords':[]}]}]};Path(sys.argv[2]).write_text(render_review_html(m))`,path.join(root,'skills/agentic-aac-board-maker/scripts'),review]);
 await page.context().setOffline(true);await page.goto(pathToFileURL(review).href);await expect(page.locator('input[value="2"]')).toBeDisabled();await page.locator('input[value="1"]').check();
 const waiting=page.waitForEvent('download');await page.getByRole('button',{name:'Download decisions'}).click();const download=await waiting;const data=JSON.parse(readFileSync(await download.path(),'utf8'));expect(data.boardFingerprint).toBe('test-revision');expect(data.entries[0].approvedSymbolId).toBe(1);
});
