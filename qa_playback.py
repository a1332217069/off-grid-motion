import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
R=Path(__file__).parent
async def main():
    errors=[]
    async with async_playwright() as p:
        b=await p.chromium.launch()
        pg=await b.new_page(viewport={'width':1440,'height':1000})
        pg.on('pageerror',lambda e:errors.append(str(e)))
        await pg.goto((R/'preview.html').as_uri())
        await pg.wait_for_function("document.querySelector('video').readyState>=2")
        await pg.evaluate("async()=>{let v=document.querySelector('video');v.muted=true;await v.play();}")
        # Wait for actual playback progress, rather than assuming a fixed decoder startup time.
        await pg.wait_for_function("document.querySelector('video').currentTime>.25",timeout=15000)
        result=await pg.evaluate('''async()=>{let v=document.querySelector('video');let advanced=v.currentTime>.25,decodedFrames=v.getVideoPlaybackQuality().totalVideoFrames;v.pause();let seeks=[];for(let t of [1.6,4.84,9.12,14.8]){v.currentTime=t;await new Promise(r=>v.addEventListener('seeked',r,{once:true}));seeks.push({target:t,actual:v.currentTime});}return {duration:v.duration,width:v.videoWidth,height:v.videoHeight,advanced,decodedFrames,seeks,error:v.error};}''')
        await pg.screenshot(path=str(R/'player-preview.jpg'))
        await b.close()
    result['page_errors']=errors
    result['pass']=result['duration']==15 and result['width']==1920 and result['height']==1080 and result['advanced'] and not result['error'] and not errors and all(abs(x['actual']-x['target'])<.05 for x in result['seeks'])
    (R/'playback-QA.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2));assert result['pass']
asyncio.run(main())
