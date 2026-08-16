import math, os, random, subprocess
from PIL import Image, ImageDraw, ImageFilter
import imageio_ffmpeg

W=H=1080; FPS=24; N=144
OUT=os.path.join(os.getcwd(),'outputs'); os.makedirs(OUT,exist_ok=True)
MP4=os.path.join(OUT,'one_patron_attractor_x_optimized_1080x1080_6s.mp4')
GIF=os.path.join(OUT,'one_patron_attractor_x_optimized_preview.gif')
random.seed(21)

cx=cy=540; R=382
gold=(205,139,63); pale=(243,194,105); blue=(86,205,255)

def clamp(x): return max(0,min(255,int(x)))
def rgba(c,a): return (*c,clamp(a))
def cd(a,b):
    d=abs(a-b)%1.0
    return min(d,1-d)
def gauss_phase(p,c,w): return math.exp(-(cd(p,c)/w)**2)
def pt(r,a): return (cx+r*math.cos(a),cy+r*math.sin(a))

# A deterministic organic, radially branching connection field.
edges=[]; nodes=[]
for trunk in range(13):
    base=-math.pi/2 + trunk*(2*math.pi/13) + random.uniform(-.08,.08)
    prev=(cx+random.uniform(-12,12),cy+random.uniform(-12,12))
    nodes.append((prev,0))
    for level in range(1,7):
        rr=level*52+random.uniform(-10,10)
        aa=base + .13*math.sin(level*.9+trunk) + random.uniform(-.045,.045)
        cur=pt(rr,aa); edges.append((prev,cur,level,trunk)); nodes.append((cur,level)); prev=cur
        if level>=2:
            for sgn in (-1,1):
                if random.random()<.72:
                    b=pt(rr+random.uniform(27,55),aa+sgn*random.uniform(.12,.28))
                    edges.append((cur,b,level+.35,trunk)); nodes.append((b,level+.35))

# Main future-to-centre path, angled slightly right of vertical.
future_a=-.68
future=pt(R-4,future_a)
main=[]
for i in range(12):
    u=i/11
    a=future_a + .055*math.sin(u*math.pi*2) * (1-u)
    r=(R-8)*(1-u)
    main.append(pt(r,a))

def draw_frame(k, size=W):
    p=k/N
    bg=Image.new('RGB',(W,H),(8,10,12))
    # faint graphite vignette / grain
    pix=bg.load()
    for y in range(0,H,3):
        for x in range(0,W,3):
            d=math.hypot(x-cx,y-cy)/760
            n=((x*17+y*31+k*0)%23)-11
            v=clamp(13-7*d+n*.10)
            for yy in range(y,min(y+3,H)):
                for xx in range(x,min(x+3,W)): pix[xx,yy]=(v,v+1,v+2)

    glow=Image.new('RGBA',(W,H)); gd=ImageDraw.Draw(glow)
    crisp=Image.new('RGBA',(W,H)); d=ImageDraw.Draw(crisp)
    breathe=1+0.009*math.sin(2*math.pi*p)

    # 21 segments and one intentional open gap near the future point.
    gap=future_a
    arc_total=2*math.pi-.27
    seg_pitch=arc_total/21
    for i in range(21):
        a0=gap+.135+i*seg_pitch+.035
        a1=gap+.135+(i+1)*seg_pitch-.035
        rr=R*breathe
        box=(cx-rr,cy-rr,cx+rr,cy+rr)
        ring_wave=math.exp(-((min(abs(i-p*21),21-abs(i-p*21)))/1.25)**2)
        pulse=.78+.14*math.sin(2*math.pi*p+i*.43)+.52*ring_wave
        col=rgba(gold,95*pulse)
        gd.arc(box,math.degrees(a0),math.degrees(a1),fill=rgba(gold,150*pulse),width=14)
        d.arc(box,math.degrees(a0),math.degrees(a1),fill=col,width=3)

    # Network subtly anticipates the attractor before it is brightest.
    attract=.5+.5*math.sin(2*math.pi*(p-.65))
    reveal=.72+.24*math.sin(2*math.pi*(p-.08))
    for a,b,level,trunk in edges:
        pull=.018*attract*(level/6)**2
        bx=b[0]*(1-pull)+future[0]*pull; by=b[1]*(1-pull)+future[1]*pull
        growth=.58+.42*max(0,math.sin(2*math.pi*p-level*.23+trunk*.08))
        alpha=(32+38*(level/7))*reveal*growth
        gd.line([a,(bx,by)],fill=rgba(gold,alpha*2.2),width=7)
        d.line([a,(bx,by)],fill=rgba(gold,alpha),width=1)

    # Delicate vertical alignment at peak, never a literal numeral.
    peak=gauss_phase(p,.23,.072)
    x1=526+8*math.sin(2*math.pi*p)
    d.line([(x1,655),(x1+6,575),(x1-2,500),(x1+4,420)],fill=rgba(pale,72*peak),width=2)
    gd.line([(x1,655),(x1+6,575),(x1-2,500),(x1+4,420)],fill=rgba(pale,135*peak),width=11)

    # Main connection path.
    gd.line(main,fill=rgba(gold,115),width=9,joint='curve')
    d.line(main,fill=rgba(pale,100),width=2,joint='curve')

    # Future point blooms after the branches have already bent.
    dot=gauss_phase(p,.985,.18)
    fx,fy=future
    gd.ellipse((fx-23,fy-23,fx+23,fy+23),fill=rgba(pale,125*dot))
    d.ellipse((fx-3-dot*3,fy-3-dot*3,fx+3+dot*3,fy+3+dot*3),fill=rgba(pale,175+70*dot))

    # Cold impulse travels from future point back to centre once per loop.
    travel=((p-.005)%1.0)/.30
    if 0<=travel<=1:
        idx=travel*(len(main)-1); ii=min(len(main)-2,int(idx)); f=idx-ii
        x=main[ii][0]*(1-f)+main[ii+1][0]*f; y=main[ii][1]*(1-f)+main[ii+1][1]*f
        gd.ellipse((x-24,y-24,x+24,y+24),fill=rgba(blue,145*math.sin(math.pi*travel)))
        d.ellipse((x-4,y-4,x+4,y+4),fill=rgba(blue,245*math.sin(math.pi*travel)))

    # Node wave follows the impulse inward.
    wave=((p-.025)%1.0)/.34
    if 0<=wave<=1:
        target=6*(1-wave)
        for (x,y),lev in nodes:
            z=math.exp(-((lev-target)/.42)**2)*math.sin(math.pi*wave)
            if z>.08:
                gd.ellipse((x-7*z,y-7*z,x+7*z,y+7*z),fill=rgba(blue,115*z))
                d.ellipse((x-1.5,y-1.5,x+1.5,y+1.5),fill=rgba(blue,190*z))

    bloom=glow.filter(ImageFilter.GaussianBlur(13))
    bg=Image.alpha_composite(bg.convert('RGBA'),bloom)
    bg=Image.alpha_composite(bg,crisp)
    return bg.convert('RGB')

ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
cmd=[ffmpeg,'-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-vcodec','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',MP4]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
gif_frames=[]
for k in range(N):
    im=draw_frame(k)
    proc.stdin.write(im.tobytes())
    if k%2==0: gif_frames.append(im.resize((540,540),Image.Resampling.LANCZOS).quantize(colors=128,method=Image.Quantize.MEDIANCUT))
proc.stdin.close(); err=proc.stderr.read().decode(); rc=proc.wait()
if rc: raise RuntimeError(err)
gif_frames[0].save(GIF,save_all=True,append_images=gif_frames[1:],duration=1000/(FPS/2),loop=0,optimize=False,disposal=2)
# Verification stills: first frame and near-peak frame.
draw_frame(0).save(os.path.join(OUT,'one_patron_frame_start.png'))
draw_frame(int(.23*N)).save(os.path.join(OUT,'one_patron_frame_peak.png'))
print(MP4); print(GIF)
