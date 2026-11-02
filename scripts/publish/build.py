# usage: python3 build.py DIGEST_DIR REPO DAY(YYYY-MM-DD) [--ov overrides.json] [--brief briefing.txt]
# Builds editions/DAY.json (with duplicate stories merged), trending/DAY.json, stars/tracked.json and layoffs/tracker.json.
import json, sys, re, datetime, os, subprocess

args = sys.argv[1:]
D, R, DAY = args[:3]
opt = {args[i]: args[i + 1] for i in range(3, len(args) - 1, 2)}
if len(args) == 4:  # old style: 4th positional arg is the overrides file
    opt["--ov"] = args[3]
OV = json.load(open(opt["--ov"])) if opt.get("--ov") else {}
BRIEF = open(opt["--brief"]).read().strip() if opt.get("--brief") else ""
DID = DAY.replace("-", "")
ORDER = ["tech-news", "chips", "ecosystem", "x-desk", "gadgets", "tech-pulse", "aws-news", "layoffs"]
PERSONAL = re.compile(r"Pradeep|\bhis\b|wedding|your feed", re.I)
NAMES = {"tech-news": "AI", "chips": "Chips & Research", "ecosystem": "Claude Ecosystem", "x-desk": "Trending on X",
         "gadgets": "Gadgets", "tech-pulse": "Pulse", "aws-news": "Cloud", "layoffs": "Layoffs"}

# ---------- load sections ----------
secs = {}
for r in ORDER:
    p = f"{D}/{r}-{DID}.json"
    if not os.path.exists(p):
        continue
    d = json.load(open(p)); d = d.get("data", d)
    if not d.get("items"):
        continue
    items = []
    for i, it in enumerate(d.get("items", [])):
        keys = ["title", "body", "why", "topics", "source", "url", "date"] + (["company", "count", "pct", "country", "location", "industry", "kind"] if r == "layoffs" else [])
        o = {k: it[k] for k in keys if k in it}
        o["source"] = o.get("source", "").replace(" · from your feed", "")
        o["_id"] = f"{r}:{i}"
        if f"{r}:{i}" in OV:
            o["why"] = OV[f"{r}:{i}"]
        if PERSONAL.search(o.get("why", "")):
            o.pop("why", None)
        items.append(o)
    secs[r] = {"routine": r, "status": d.get("status"), "headline": d.get("headline", ""),
               "filed": d.get("end") or d.get("start"), "note": d.get("note", ""), "items": items}
    if re.search(r"Pradeep", secs[r]["headline"] + secs[r]["note"]):
        raise SystemExit(f"personal text in {r} headline/note")

# ---------- merge duplicate stories ----------
STOP = set("a an the and or of to in on for with by from at as is are be its it this that new now via into over up out after vs than more most first".split())
def norm_url(u):
    u = str(u or "").strip().lower()
    u = re.sub(r"^https?://(www\.|m\.|mobile\.)?", "", u)
    u = re.sub(r"[?#].*$", "", u).rstrip("/")
    u = u.replace("twitter.com/", "x.com/")
    return u
def words(t):
    return {w for w in re.findall(r"[a-z0-9][a-z0-9.\-]*", str(t).lower()) if w not in STOP and len(w) > 1}
def key_terms(t):  # names with digits or capitals carry the story identity (Haiku 5.5, GB300, Kimi K3.1)
    return {w.lower() for w in re.findall(r"\b[A-Za-z]*\d[\w.\-]*\b|\b[A-Z][a-zA-Z]{2,}\b", str(t))}
def same_story(a, b):
    ua, ub = norm_url(a.get("url")), norm_url(b.get("url"))
    if ua and ua == ub:
        return True
    wa, wb = words(a.get("title")), words(b.get("title"))
    if not wa or not wb:
        return False
    j = len(wa & wb) / len(wa | wb)
    ka, kb = key_terms(a.get("title")) - STOP, key_terms(b.get("title")) - STOP
    shared_keys = ka & kb
    return (j >= 0.5 and len(wa & wb) >= 3) or (j >= 0.3 and len(shared_keys) >= 2 and any(re.search(r"\d", k) for k in shared_keys))

kept, merges = [], []
# judged merges from the overrides file: {"merge": [["x-desk:0", "tech-news:0"], ...]} (duplicate, keeper)
byid = {it["_id"]: (r, it) for r in secs for it in secs[r]["items"]}
for dup, tgt in OV.get("merge", []):
    if dup in byid and tgt in byid and dup != tgt:
        (rd, d_it), (rt, t_it) = byid[dup], byid[tgt]
        t_it.setdefault("also", []).append({"section": NAMES[rd], "source": d_it.get("source", ""), "url": d_it.get("url", "")})
        secs[rd]["items"] = [x for x in secs[rd]["items"] if x is not d_it]
        merges.append(f"(judged) {NAMES[rd]}: {d_it['title'][:60]}  ->  {NAMES[rt]}: {t_it['title'][:60]}")
for r in ORDER:
    if r not in secs:
        continue
    keep = []
    for it in secs[r]["items"]:
        hit = next((k for k in kept if same_story(k[1], it)), None)
        if hit and r != hit[0]:
            hit[1].setdefault("also", []).append({"section": NAMES[r], "source": it.get("source", ""), "url": it.get("url", "")})
            merges.append(f"{NAMES[r]}: {it['title'][:60]}  ->  {NAMES[hit[0]]}: {hit[1]['title'][:60]}")
            continue
        keep.append(it); kept.append((r, it))
    secs[r]["items"] = keep
secs = {r: v for r, v in secs.items() if v["items"]}
for m in merges:
    print("merged", m)

for v in secs.values():
    for it in v["items"]:
        it.pop("_id", None)

# ---------- write the edition ----------
ed = {"date": DAY, "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "sections": secs}
if BRIEF:
    ed["briefing"] = BRIEF
s = json.dumps(ed, indent=1, ensure_ascii=False)
assert not re.search(r"Pradeep|your feed|wedding", s, re.I), "personal text left"
open(f"{R}/editions/{DAY}.json", "w").write(s)
ix = json.load(open(f"{R}/editions/index.json"))
ix["editions"] = [e for e in ix["editions"] if e["date"] != DAY]
first = (secs.get("tech-news") or next(iter(secs.values())))["items"][0]["title"]
n = sum(len(v["items"]) for v in secs.values())
ix["editions"].append({"date": DAY, "stories": n, "headline": first})
ix["editions"].sort(key=lambda e: e["date"], reverse=True)
json.dump(ix, open(f"{R}/editions/index.json", "w"), indent=1, ensure_ascii=False)
print(DAY, n, "stories |", len(merges), "merged |", first, "| briefing" if BRIEF else "")

# ---------- trending page export ----------
trend = None
tp = f"{D}/trending-{DID}.json"
if os.path.exists(tp):
    t = json.load(open(tp)); t = t.get("data", t)
    if t.get("periods"):
        os.makedirs(f"{R}/trending", exist_ok=True)
        trend = {"date": DAY, "generated": ed["generated"], "headline": t.get("headline", ""), "periods": {}}
        for p in ["daily", "weekly", "monthly"]:
            v = t["periods"].get(p) or {}
            trend["periods"][p] = {"topics": [str(x) for x in (v.get("topics") or [])][:6],
                                   "repos": [{k: r.get(k) for k in ["repo", "url", "description", "kind", "language", "stars", "gained", "source"]}
                                             for r in (v.get("repos") or [])][:10]}
        s2 = json.dumps(trend, indent=1, ensure_ascii=False)
        assert not PERSONAL.search(s2), "personal text in trending"
        open(f"{R}/trending/{DAY}.json", "w").write(s2)
        ip = f"{R}/trending/index.json"
        dates = json.load(open(ip))["dates"] if os.path.exists(ip) else []
        json.dump({"dates": sorted(set(dates) | {DAY}, reverse=True)}, open(ip, "w"), indent=1)
        print("trending", DAY, {p: len(trend["periods"][p]["repos"]) for p in trend["periods"]})

# ---------- star tracker: list of repos to follow ----------
os.makedirs(f"{R}/stars", exist_ok=True)
tk = f"{R}/stars/tracked.json"
tracked = json.load(open(tk)) if os.path.exists(tk) else {"repos": {}}
def track(repo, kind, desc, where, stars=None):
    repo = repo.strip().strip("/")
    if not re.fullmatch(r"[\w.\-]+/[\w.\-]+", repo) or repo.lower().endswith((".git",)):
        return
    e = tracked["repos"].setdefault(repo, {"first_seen": DAY, "kind": kind or "Other", "description": desc or "", "seen_in": []})
    e["last_seen"] = DAY
    if kind and e.get("kind") in (None, "", "Other"):
        e["kind"] = kind
    if desc and not e.get("description"):
        e["description"] = desc
    if where not in e["seen_in"]:
        e["seen_in"] = (e["seen_in"] + [where])[-6:]
    if isinstance(stars, int):
        e.setdefault("reported", {})[DAY] = stars
if trend:
    for p in trend["periods"].values():
        for r in p["repos"]:
            track(str(r.get("repo") or ""), r.get("kind"), r.get("description"), "Trending", r.get("stars"))
KIND_BY_TOPIC = {"Skills": "Skill", "Plugins": "Plugin", "MCP": "MCP server", "Hooks": "Hook", "Subagents": "Subagent"}
for r, sec in secs.items():
    for it in sec["items"]:
        m = re.match(r"https?://github\.com/([\w.\-]+/[\w.\-]+)", str(it.get("url") or ""))
        if m and not m.group(1).split("/")[1] in ("releases", "issues", "pulls"):
            kind = next((KIND_BY_TOPIC[t] for t in it.get("topics", []) if t in KIND_BY_TOPIC), None)
            track(m.group(1), kind, it.get("title"), NAMES[r])
json.dump(tracked, open(tk, "w"), indent=1, ensure_ascii=False)
print("tracked repos:", len(tracked["repos"]))

# ---------- layoffs tracker (layoffs/tracker.json) ----------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import layoffs as LAY
lay_items = (secs.get("layoffs") or {}).get("items", [])
added = LAY.merge_items(R, lay_items, DAY) if lay_items else 0
subprocess.run(["git", "-C", R, "add", "layoffs"], check=False)
print("layoffs tracker: +%d new" % added)
