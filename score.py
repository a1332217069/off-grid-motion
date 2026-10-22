"""Original score for OFF GRID. No samples, external tracks or paid services.
Run in the installed onetake Python runtime. Fixed seed, 48 kHz stereo.
"""
import json, sys, wave, subprocess
from pathlib import Path
import numpy as np
from scipy import signal
sys.path.insert(0, str(Path(__file__).parent/'tools'))
from sfx_palette import Score, air, wood, sub, glass, SR, lp, hp

ROOT=Path(__file__).parent
score=Score(dur=15,T60=.35)
rng=np.random.default_rng(231)
events=json.loads((ROOT/'events.json').read_text())

def bass(freq,dur=.31):
    t=np.arange(int(SR*dur))/SR
    # A rounded, plucked electronic bass. The detuned partial is quieter than the fundamental.
    phase=2*np.pi*freq*t
    env=(1-np.exp(-t*180))*np.exp(-t*12)
    return lp((np.sin(phase)+.22*np.sin(phase*2.003)+.12*np.sin(phase*3))*env,1100)

def tick(dur=.09):
    t=np.arange(int(SR*dur))/SR
    return hp(rng.standard_normal(len(t)),7000)*np.exp(-t*90)*.12

def chord(dur=.9):
    t=np.arange(int(SR*dur))/SR
    s=sum(np.sin(2*np.pi*f*t+np.sin(2*np.pi*f*.5*t)*.10)*a
          for f,a in [(146.832,.5),(220,.20),(293.665,.13),(349.228,.10)])
    return lp(s,2100)*(1-np.exp(-t*120))*np.exp(-t*5)

for e in events:
    t,k,x,a=e['t'],e['kind'],e['x'],e['strength']
    pan=(x/1920*2-1)*.55
    if k=='hit':
        score.place(sub(52,.55),t,gain=.43*a,pan=pan,send=.13)
        score.place(wood(155,.14),t,gain=.28*a,pan=pan,send=.08)
    elif k in ('hinge','fold'):
        score.place(wood(230 if k=='hinge' else 145,.14),t,gain=.22*a,pan=pan,send=.18)
    elif k in ('air','suck'):
        d=.52 if k=='air' else .65
        score.place(air(d,350,3300 if k=='air' else 130,1.1,.6),max(.0,t-d*.8),gain=.20*a,pan=-pan,pan_to=pan,send=.10)
    elif k=='type':
        score.place(sub(58,.28),t,gain=.43*a,pan=pan*.3,send=.12)
        score.place(wood(310,.08),t,gain=.28*a,pan=pan,send=.15)
    elif k=='seal':
        score.place(wood(210,.10),t,gain=.16*a,pan=pan,send=.12)

# A syncopated D-minor pulse spine. The pause is composed into picture and sound.
step=60/118/2
notes=[73.416,0,73.416,110,0,87.307,73.416,0,146.832,110,0,87.307]
for n in range(23):
    t=1.60+n*step
    if t>7.14: break
    f=notes[n%len(notes)]
    if f:
        score.place(bass(f),t,gain=.19 if n%4 else .25,pan=-.12 if n%2 else .12,send=.035)
    if n%2==1:
        score.place(tick(),t+.012,gain=.55,pan=(-1 if n%4==1 else 1)*.38,send=.12)
for t in [2.65,4.84,6.16,10.53,12.16]:
    score.place(chord(.72),t,gain=.14,pan=0,send=.14)
score.place(glass(880,.52,.15),12.72,gain=.035,pan=-.2,send=.13)
score.write(str(ROOT/'score.wav'))
# The audio render is mastered separately from synthesis, retaining the authored silence.
subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(ROOT/'score.wav'),
                '-af','loudnorm=I=-16:TP=-4:LRA=8','-ar','48000','-c:a','pcm_s16le',
                str(ROOT/'score-master.wav')],check=True)
(ROOT/'score-master.wav').replace(ROOT/'score.wav')
print('Original score written:',ROOT/'score.wav')
