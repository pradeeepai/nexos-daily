# usage: python3 week.py REPO picks.json  -> writes weekly/<week_end>.json and weekly/index.json
# picks.json: {week_start, week_end, intro, top:[[date, title-prefix], ...], models:[{name, lab, what, date, url|ref:[date,title-prefix]}],
#              skills:[repo, ...] (looked up in trending/<week_end>.json, then stars/history.json and stars/tracked.json),
#              chips:[[date,title-prefix],...], skill_of_week:{name, kind, url, stars, what, install, verdict, note}}
# See weekly/2026-11-01.json for a finished example.
import json, sys, os, re
R, PK = sys.argv[1:3]
pk = json.load(open(PK))
eds = {}
for f in os.listdir(f"{R}/editions"):
    if re.match(r"\d{4}-\d{2}-\d{2}\.json$", f) and pk["week_start"] <= f[:10] <= pk["week_end"]:
        eds[f[:10]] = json.load(open(f"{R}/editions/{f}"))
NAMES = {"tech-news": "AI", "chips": "Chips & Research", "ecosystem": "Claude Ecosystem", "x-desk": "Trending on X", "gadgets": "Gadgets", "tech-pulse": "Pulse", "aws-news": "Cloud", "layoffs": "Layoffs"}
def find(date, prefix):
    for r, sec in eds[date]["sections"].items():
        for it in sec["items"]:
            if it["title"].lower().startswith(prefix.lower()):
                return r, it
    raise SystemExit(f"not found: {date} {prefix}")
def first_sentences(t, n=2):
    parts = re.split(r"(?<=[.!?])\s+", str(t or "").strip())
    return " ".join(parts[:n])
out = {k: pk[k] for k in ("week_start", "week_end", "intro") if k in pk}
out["top"] = []
for date, prefix in pk.get("top", []):
    r, it = find(date, prefix)
    out["top"].append({"title": it["title"], "body": first_sentences(it.get("body")), "section": NAMES[r], "url": it.get("url", ""), "date": date})
out["models"] = []
for m in pk.get("models", []):
    if "ref" in m:
        r, it = find(*m.pop("ref")); m.setdefault("url", it.get("url", "")); m.setdefault("what", first_sentences(it.get("body"), 1))
    out["models"].append(m)
out["chips"] = []
for date, prefix in pk.get("chips", []):
    r, it = find(date, prefix)
    out["chips"].append({"title": it["title"], "body": first_sentences(it.get("body"), 1), "url": it.get("url", ""), "date": date})
trend = json.load(open(f"{R}/trending/{pk['week_end']}.json")) if os.path.exists(f"{R}/trending/{pk['week_end']}.json") else {"periods": {}}
weekly = {r["repo"]: r for p in ("monthly", "daily", "weekly") for r in trend["periods"].get(p, {}).get("repos", []) if r.get("repo")}
hist = json.load(open(f"{R}/stars/history.json")).get("repos", {}) if os.path.exists(f"{R}/stars/history.json") else {}
tracked = json.load(open(f"{R}/stars/tracked.json")).get("repos", {}) if os.path.exists(f"{R}/stars/tracked.json") else {}
out["skills"] = []
for repo in pk.get("skills", []):
    r, h, t = weekly.get(repo, {}), hist.get(repo, {}), tracked.get(repo, {})
    ser = sorted(h.get("s", {}).items())
    ser = [x for x in ser if pk["week_start"] <= x[0] <= pk["week_end"]] or ser
    gained = ser[-1][1] - ser[0][1] if len(ser) > 1 else r.get("gained")
    out["skills"].append({"repo": repo, "url": r.get("url") or h.get("url") or f"https://github.com/{repo}", "kind": r.get("kind") or h.get("kind") or t.get("kind", ""),
                          "description": r.get("description") or h.get("description") or t.get("description", ""),
                          "stars": (ser[-1][1] if ser else r.get("stars")), "gained": gained})
out["skills"].sort(key=lambda s: -(s.get("gained") or 0))
if pk.get("skill_of_week"):
    out["skill_of_week"] = pk["skill_of_week"]
s = json.dumps(out, indent=1, ensure_ascii=False)
assert not re.search(r"Pradeep|your feed|wedding", s, re.I)
os.makedirs(f"{R}/weekly", exist_ok=True)
open(f"{R}/weekly/{pk['week_end']}.json", "w").write(s)
ip = f"{R}/weekly/index.json"
weeks = json.load(open(ip))["weeks"] if os.path.exists(ip) else []
json.dump({"weeks": sorted(set(weeks) | {pk["week_end"]}, reverse=True)}, open(ip, "w"), indent=1)
print("weekly", pk["week_end"], {k: len(out[k]) for k in ("top", "models", "chips", "skills")})
