"""Make audio/DAY.mp3 from the newest edition's briefing text with Kokoro TTS. Runs in GitHub Actions."""
# Needs preshed<=3.0.13 (pinned in the workflow).
import json, os, glob, subprocess, datetime, time, traceback, re
def gh_error(msg):  # shows as an annotation on the run
    print("::error::" + msg.replace("\n", "%0A")[-3000:], flush=True)
try:
    import numpy as np, soundfile as sf
    from kokoro import KPipeline
except Exception:
    gh_error(traceback.format_exc()); raise

eds = sorted(glob.glob("editions/20*.json"))
todo = []
for p in eds[-3:]:
    day = os.path.basename(p)[:-5]
    e = json.load(open(p))
    if e.get("briefing") and (not os.path.exists(f"audio/{day}.mp3") or os.path.getmtime(p) > os.path.getmtime(f"audio/{day}.mp3")):
        todo.append((day, e["briefing"]))
if not todo:
    print("nothing to do"); raise SystemExit(0)
for n in range(4):  # model download from Hugging Face can fail for a short time
    try:
        pipe = KPipeline(lang_code="a"); break
    except Exception:
        gh_error(traceback.format_exc()); time.sleep(20 * (n + 1))
else:
    raise SystemExit("could not load Kokoro")
os.makedirs("audio", exist_ok=True)
failed = []
for day, text in todo:
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)
    try:
        chunks = [a.numpy() if hasattr(a, "numpy") else a for _, _, a in pipe(text, voice="af_heart", speed=1.0) if a is not None]
        if not chunks:
            raise RuntimeError("no audio")
    except Exception:
        gh_error(traceback.format_exc()); failed.append(day); continue
    sf.write("/tmp/b.wav", np.concatenate(chunks), 24000)
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "/tmp/b.wav", "-ac", "1", "-b:a", "48k", f"audio/{day}.mp3"], capture_output=True, text=True)
    if r.returncode:
        gh_error("ffmpeg: " + r.stderr); failed.append(day); continue
    print("made", day)
cut = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
for f in glob.glob("audio/20*.mp3"):
    if os.path.basename(f)[:10] < cut:
        os.remove(f); print("removed", f)
json.dump({"days": sorted(os.path.basename(f)[:10] for f in glob.glob("audio/20*.mp3"))}, open("audio/index.json", "w"))
if failed:
    raise SystemExit(f"failed: {failed}")
