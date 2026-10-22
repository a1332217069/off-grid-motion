"""Checks the rendered composition, arbitrary seeks, frames, rest and offline loading."""
import asyncio, hashlib, json, math, random
from pathlib import Path
from playwright.async_api import async_playwright

ROOT=Path(__file__).parent
async def main():
    errors=[]; external=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        page=await browser.new_page(viewport={'width':1920,'height':1080})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:external.append(r.url) if r.url.startswith(('https:','http:')) else None)
        await page.goto((ROOT/'comp.html').as_uri());await page.evaluate('window.__ready')
        events=await page.evaluate('window.__events()')
        (ROOT/'events.json').write_text(json.dumps(events,indent=2),encoding='utf-8')
        checks=[]
        for t in [0,.65,1.58,2.10,3.52,4.60,5.60,6.80,7.80,9.30,9.70,11.50,14]:
            await page.evaluate('(t)=>window.__seek(t)',t)
            a=hashlib.sha256(await page.locator('#film').screenshot()).hexdigest()
            await page.evaluate('window.__seek(14.9)');await page.evaluate('window.__seek(.123)')
            await page.evaluate('(t)=>window.__seek(t)',t)
            b=hashlib.sha256(await page.locator('#film').screenshot()).hexdigest()
            checks.append({'t':t,'equal':a==b})
        # Every authored frame must evaluate to finite positions and no exceptions.
        frame_qa=await page.evaluate('''()=>{let bad=[];for(let i=0;i<=900;i++){let t=i/60;window.__seek(t);for(let [id,b] of Object.entries(window.__track(t))){if(![b.x,b.y,b.w,b.h,b.op].every(Number.isFinite))bad.push([t,id]);}}return {samples:901,bad};}''')
        await page.evaluate('window.__seek(14)');await page.screenshot(path=str(ROOT/'poster.png'))
        rest=[]
        for ta,tb in [(0,.5),(7.5,8.4),(13.2,14.9)]:
            await page.evaluate('(t)=>window.__seek(t)',ta);a=await page.locator('#film').screenshot()
            await page.evaluate('(t)=>window.__seek(t)',tb);b=await page.locator('#film').screenshot()
            rest.append({'window':[ta,tb],'pixel_identical':a==b})
        await page.goto((ROOT/'comp.html').as_uri()+'?play');await page.evaluate('window.__ready')
        await page.wait_for_timeout(250)
        await page.keyboard.press('Space')
        paused=await page.locator('#play').inner_text()=='PLAY'
        await page.locator('#scrub').fill('6.5')
        scrub_ok=await page.locator('#clock').inner_text()=='06.50 / 15'
        await page.keyboard.press('ArrowRight')
        keys_ok=await page.locator('#clock').inner_text()=='06.60 / 15'
        await page.locator('#audioBtn').click();audio_ok=await page.locator('#audioBtn').inner_text()=='SOUND OFF'
        await browser.close()
    result={'duration':15,'resolution':[1920,1080],'page_errors':errors,'external_requests':external,'deterministic':checks,'full_timeline':frame_qa,'rests':rest,'player':{'pause':paused,'scrub':scrub_ok,'keyboard':keys_ok,'sound_button':audio_ok}}
    passed=not errors and not external and all(c['equal'] for c in checks) and not frame_qa['bad'] and all([paused,scrub_ok,keys_ok,audio_ok]) and all(r['pixel_identical'] for r in rest)
    result['pass']=passed
    (ROOT/'QA.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2));assert passed
if __name__=='__main__':asyncio.run(main())
