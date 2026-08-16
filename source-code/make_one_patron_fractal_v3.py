import math, os, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageStat
import imageio_ffmpeg

W = H = 1080
FPS, N = 24, 144
CX = CY = 540
OUT = os.path.join(os.getcwd(), "outputs")
os.makedirs(OUT, exist_ok=True)
MP4 = os.path.join(OUT, "one_patron_fractal_unfolding_1080x1080_6s.mp4")
GIF = os.path.join(OUT, "one_patron_fractal_unfolding_preview.gif")

GOLD = (205, 137, 61)
PALE = (255, 204, 112)
BLUE = (74, 207, 255)
RING_R = 395
FUTURE_A = -0.64
FUTURE = (CX + RING_R * math.cos(FUTURE_A), CY + RING_R * math.sin(FUTURE_A))

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(x):
    x = clamp(x)
    return x*x*(3-2*x)
def rgba(c, a): return (*c, max(0, min(255, int(a))))
def cdist(a, b):
    d = abs(a-b) % 1.0
    return min(d, 1.0-d)
def phase_gauss(p, center, width): return math.exp(-(cdist(p, center)/width)**2)

# Quiet graphite background, fixed across frames so the seam is exact.
yy, xx = np.mgrid[0:H, 0:W]
rr = np.sqrt((xx-CX)**2 + (yy-CY)**2) / 760.0
rng = np.random.default_rng(21)
grain = rng.normal(0, 0.75, (H, W))
base = np.clip(13.0 - 8.0*rr + grain, 5, 14)
bg_arr = np.dstack((base*.78, base*.86, base)).astype(np.uint8)
BACKGROUND = Image.fromarray(bg_arr, "RGB")

# A real recursive binary structure: one trunk, then 2, 4, 8, 16...
random.seed(21)
nodes = []
edges = []

def add_node(x, y, depth, parent=-1):
    idx = len(nodes)
    nodes.append({"x": x, "y": y, "depth": depth, "parent": parent})
    return idx

root = add_node(CX, 748, 0)
trunk = add_node(CX, 624, 0, root)
edges.append((root, trunk, 0))

def branch(parent, angle, length, depth, handed):
    if depth > 7:
        return
    p = nodes[parent]
    # Repeated proportions produce visible self-similarity; tiny variation keeps it alive.
    jitter = random.uniform(-0.035, 0.035)
    x = p["x"] + length * math.cos(angle + jitter)
    y = p["y"] + length * math.sin(angle + jitter)
    child = add_node(x, y, depth, parent)
    edges.append((parent, child, depth))
    if depth < 7:
        spread = 0.43 + 0.025*math.sin(depth*1.7 + handed)
        shrink = 0.735
        branch(child, angle-spread, length*shrink, depth+1, -1)
        branch(child, angle+spread, length*shrink, depth+1, 1)

branch(trunk, -math.pi/2-0.28, 118, 1, -1)
branch(trunk, -math.pi/2+0.28, 118, 1, 1)

# The endpoint nearest the future attractor defines a genuine path back to the root.
children = {i: [] for i in range(len(nodes))}
for a, b, d in edges: children[a].append(b)
leaves = [i for i in range(len(nodes)) if not children[i]]
tip = min(leaves, key=lambda i: (nodes[i]["x"]-FUTURE[0])**2 + (nodes[i]["y"]-FUTURE[1])**2)
path_ids = []
i = tip
while i >= 0:
    path_ids.append(i)
    i = nodes[i]["parent"]
path_ids.reverse()

def growth_at(p):
    if p < .43: return smooth(p/.43)
    if p < .72: return 1.0
    return smooth((1-p)/.28)

def deformed_positions(p):
    # Pull begins well before the future point blooms.
    anticipation = smooth((p-.16)/.19) * (1-smooth((p-.66)/.20))
    pos = []
    for n in nodes:
        depth = n["depth"]
        right = smooth((n["x"]-(CX-100))/340)
        influence = anticipation * right * (depth/7)**1.65 * .105
        x = n["x"] + (FUTURE[0]-n["x"])*influence
        y = n["y"] + (FUTURE[1]-n["y"])*influence
        pos.append((x, y))
    return pos

def draw_frame(k):
    # Start a fraction into the cycle so the first autoplay frame already contains a living seed.
    p = (k/N + .055) % 1.0
    growth = growth_at(p)
    pos = deformed_positions(p)
    crisp = Image.new("RGBA", (W, H))
    glow = Image.new("RGBA", (W, H))
    d, gd = ImageDraw.Draw(crisp), ImageDraw.Draw(glow)

    # The ring is a quiet container: exactly 21 segments and one open gap.
    breathe = 1 + .008*math.sin(2*math.pi*p)
    radius = RING_R*breathe
    box = (CX-radius, CY-radius, CX+radius, CY+radius)
    arc_total = 2*math.pi-.30
    pitch = arc_total/21
    for s in range(21):
        a0 = FUTURE_A+.15+s*pitch+.032
        a1 = FUTURE_A+.15+(s+1)*pitch-.032
        ring_distance = min(abs(s-p*21), 21-abs(s-p*21))
        wave = math.exp(-(ring_distance/1.05)**2)
        alpha = 40 + 48*wave
        gd.arc(box, math.degrees(a0), math.degrees(a1), fill=rgba(GOLD, alpha*1.7), width=11)
        d.arc(box, math.degrees(a0), math.degrees(a1), fill=rgba(GOLD, alpha), width=2)

    # Recursive unfolding, level by level. Partial tips visibly grow from their parents.
    level_cursor = growth*8.05
    for a, b, depth in edges:
        f = clamp(level_cursor-depth)
        if f <= 0: continue
        ax, ay = pos[a]; bx, by = pos[b]
        ex, ey = ax+(bx-ax)*smooth(f), ay+(by-ay)*smooth(f)
        depth_fade = 1-.045*depth
        alpha = (102 if depth == 0 else 78)*depth_fade
        width = max(1, 3-depth//3)
        gd.line([(ax,ay),(ex,ey)], fill=rgba(GOLD, alpha*2), width=9 if depth<2 else 6)
        d.line([(ax,ay),(ex,ey)], fill=rgba(PALE if depth<2 else GOLD, alpha), width=width)

    # Future point appears only after the geometry has already begun to yield to it.
    dot = phase_gauss(p, .45, .14)
    fx, fy = FUTURE
    gd.ellipse((fx-28,fy-28,fx+28,fy+28), fill=rgba(PALE, 150*dot))
    if dot > .02:
        r = 3+5*dot
        d.ellipse((fx-r,fy-r,fx+r,fy+r), fill=rgba(PALE, 150+105*dot))

    # Build the deformed future-to-root polyline.
    path = [FUTURE] + [pos[i] for i in reversed(path_ids)]
    if growth > .86:
        gd.line(path, fill=rgba(GOLD, 58*dot), width=8, joint="curve")
        d.line(path, fill=rgba(PALE, 54*dot), width=1, joint="curve")

    # Cold impulse travels from the future point backwards through the actual tree.
    travel = (p-.48)/.18
    if 0 <= travel <= 1:
        lens = [math.dist(path[j], path[j+1]) for j in range(len(path)-1)]
        total = sum(lens); target = travel*total; acc = 0
        x = y = 0
        for j, ln in enumerate(lens):
            if acc+ln >= target:
                q = (target-acc)/ln
                x = path[j][0]*(1-q)+path[j+1][0]*q
                y = path[j][1]*(1-q)+path[j+1][1]*q
                break
            acc += ln
        amp = math.sin(math.pi*travel)
        gd.ellipse((x-30,y-30,x+30,y+30), fill=rgba(BLUE, 175*amp))
        d.ellipse((x-5,y-5,x+5,y+5), fill=rgba(BLUE, 255*amp))

        # A radial reply: nearby nodes flash as the impulse passes inward.
        target_r = math.dist(FUTURE,(CX,CY))*(1-travel)
        for idx, (nx,ny) in enumerate(pos):
            nr = math.dist((nx,ny),(CX,CY))
            z = math.exp(-((nr-target_r)/27)**2)*amp
            if z > .08:
                gd.ellipse((nx-8*z,ny-8*z,nx+8*z,ny+8*z), fill=rgba(BLUE, 125*z))
                d.ellipse((nx-2,ny-2,nx+2,ny+2), fill=rgba(BLUE, 210*z))

    # At the peak the original trunk briefly dominates: a structural hint of I, not a glyph.
    one = phase_gauss(p, .63, .045)
    if one > .02:
        a, b = pos[root], pos[trunk]
        gd.line([a,b], fill=rgba(PALE, 190*one), width=15)
        d.line([a,b], fill=rgba(PALE, 175*one), width=3)

    bloom = glow.filter(ImageFilter.GaussianBlur(14))
    out = Image.alpha_composite(BACKGROUND.convert("RGBA"), bloom)
    out = Image.alpha_composite(out, crisp)
    return out.convert("RGB")

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
cmd = [ffmpeg, "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
       "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an", "-vcodec", "libx264",
       "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", MP4]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
gif_frames = []
for k in range(N):
    frame = draw_frame(k)
    proc.stdin.write(frame.tobytes())
    if k % 2 == 0:
        gif_frames.append(frame.resize((540,540), Image.Resampling.LANCZOS).quantize(colors=128))
proc.stdin.close(); err = proc.stderr.read().decode(); rc = proc.wait()
if rc: raise RuntimeError(err)
gif_frames[0].save(GIF, save_all=True, append_images=gif_frames[1:], duration=1000/(FPS/2), loop=0, disposal=2)

start = draw_frame(0)
peak = draw_frame(int(.57*N))
end_equivalent = draw_frame(N)
start.save(os.path.join(OUT, "one_patron_fractal_v3_start.png"))
peak.save(os.path.join(OUT, "one_patron_fractal_v3_peak.png"))
diff = ImageStat.Stat(ImageChops.difference(start, end_equivalent)).mean
print(MP4)
print(GIF)
print("seam_mean_abs_diff", diff)
