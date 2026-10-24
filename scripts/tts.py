"""Make audio/DAY.mp3 from the newest edition's briefing text with Kokoro TTS. Runs in GitHub Actions."""
import json, os, glob, subprocess, datetime
import numpy as np, soundfile as sf
from kokoro import KPipeline

eds = sorted(glob.glob("editions/20*.json"))
todo = []
for p in eds[-3:]:
    day = os.path.basename(p)[:-5]
    e = json.load(open(p))
    if e.get("briefing") and (not os.path.exists(f"audio/{day}.mp3") or os.path.getmtime(p) > os.path.getmtime(f"audio/{day}.mp3")):
        todo.append((day, e["briefing"]))
if not todo:
    print("nothing to do"); raise SystemExit(0)
pipe = KPipeline(lang_code="a")
os.makedirs("audio", exist_ok=True)
for day, text in todo:
    chunks = [a for _, _, a in pipe(text, voice="af_heart", speed=1.0)]
    sf.write("/tmp/b.wav", np.concatenate(chunks), 24000)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "/tmp/b.wav", "-ac", "1", "-b:a", "48k", f"audio/{day}.mp3"], check=True)
    print("made", day)
cut = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
for f in glob.glob("audio/20*.mp3"):
    if os.path.basename(f)[:10] < cut:
        os.remove(f); print("removed", f)
json.dump({"days": sorted(os.path.basename(f)[:10] for f in glob.glob("audio/20*.mp3"))}, open("audio/index.json", "w"))
