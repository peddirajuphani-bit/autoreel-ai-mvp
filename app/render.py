from pathlib import Path
import shutil, subprocess, tempfile
from .config import settings

_COLORS=["0x111827","0x172554","0x3f1d68","0x0f3d3e","0x422006","0x3f0d12","0x052e16"]

def ffmpeg_exe():
    p=shutil.which("ffmpeg")
    if p: return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise RuntimeError("FFmpeg not found. Install FFmpeg or run: pip install imageio-ffmpeg")

def has_drawtext():
    r=subprocess.run([ffmpeg_exe(),"-hide_banner","-filters"],capture_output=True,text=True)
    return " drawtext " in r.stdout

def esc(s): return s.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")

def find_font():
    candidates = [
        Path(__file__).resolve().parent.parent / "fonts" / "DejaVuSans-Bold.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ]
    for c in candidates:
        if c.exists(): return str(c)
    raise RuntimeError("DejaVuSans-Bold.ttf font not found; place it under ./fonts/")

def esc_fp(p): return p.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

def wrap_text(draw, text, font, max_width):
    lines=[]
    for word in text.split():
        if not lines: lines.append(word); continue
        trial=" ".join([lines[-1],word])
        if draw.textlength(trial,font=font)<=max_width: lines[-1]=trial
        else: lines.append(word)
    return lines

def fade_vf(duration):
    return f"fade=t=in:st=0:d=0.35,fade=t=out:st={max(0.1,duration-0.35):.2f}:d=0.35"

def make_card(path, headline, color):
    from PIL import Image, ImageDraw, ImageFont
    hexcolor=f"#{color[2:]}"
    img=Image.new("RGB",(1080,1920),hexcolor)
    d=ImageDraw.Draw(img)
    font=ImageFont.truetype(find_font(),72)
    lines=wrap_text(d,headline,font,880)
    heights=[d.textbbox((0,0),l,font=font)[3]-d.textbbox((0,0),l,font=font)[1] for l in lines]
    total=sum(heights)+18*(len(lines)-1)
    y=(1920-total)/2
    for line,h in zip(lines,heights):
        w=d.textbbox((0,0),line,font=font)[2]
        d.text(((1080-w)/2,y),line,font=font,fill="white")
        y+=h+18
    img.save(path)

def render_scene_fallback(i, s, td):
    card=Path(td)/f"card{i}.png"
    make_card(card,s.headline,_COLORS[i%len(_COLORS)])
    clip=Path(td)/f"s{i}.mp4"
    vf=fade_vf(s.duration)
    cmd=[ffmpeg_exe(),"-y","-loop","1","-framerate","30","-i",str(card),
         "-t",str(s.duration),"-vf",vf,"-c:v","libx264","-pix_fmt","yuv420p",str(clip)]
    subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return clip

def render(reel):
    outdir = Path(settings.storage_dir); outdir.mkdir(parents=True, exist_ok=True)
    target = outdir / f"reel-{reel.id}.mp4"
    with tempfile.TemporaryDirectory() as td:
        clips=[]
        use_drawtext=has_drawtext()
        for i,s in enumerate(reel.scenes):
            clip=Path(td)/f"s{i}.mp4"
            if use_drawtext:
                vf=(f"drawtext=fontfile={esc_fp(find_font())}:"
                    f"text='{esc(s.headline)}':fontcolor=white:fontsize=72:line_spacing=18:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.25:boxborderw=45,"
                    f"{fade_vf(s.duration)}")
                cmd=[ffmpeg_exe(),"-y","-f","lavfi","-i",f"color=c={_COLORS[i%len(_COLORS)]}:s=1080x1920:d={s.duration}",
                     "-vf",vf,"-r","30","-c:v","libx264","-pix_fmt","yuv420p",str(clip)]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                clip=render_scene_fallback(i,s,td)
            clips.append(clip)
        concat=Path(td)/"list.txt"
        concat.write_text("".join(f"file '{p}'\n" for p in clips))
        subprocess.run([ffmpeg_exe(),"-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(target)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return str(target)

