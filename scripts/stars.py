"""Daily star snapshot for every repo in stars/tracked.json. Runs in GitHub Actions."""
import json, os, datetime, urllib.request, urllib.error

TOKEN = os.environ.get("GITHUB_TOKEN", "")
today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d")
tracked = json.load(open("stars/tracked.json"))["repos"]
hp = "stars/history.json"
hist = json.load(open(hp)) if os.path.exists(hp) else {"repos": {}}

def get(repo):
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}", headers={"Accept": "application/vnd.github+json", "User-Agent": "nexos-daily", **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return {"_status": e.code}
    except Exception:
        return None

ok = gone = 0
for repo, meta in tracked.items():
    h = hist["repos"].setdefault(repo, {"s": {}})
    for k in ("kind", "first_seen", "seen_in"):
        if meta.get(k):
            h[k] = meta[k]
    for d, v in (meta.get("reported") or {}).items():
        h["s"].setdefault(d, v)
    d = get(repo)
    if not d:
        continue
    if d.get("_status") == 404:
        h["gone"] = True; gone += 1
        continue
    if "stargazers_count" not in d:
        continue
    h["s"][today] = d["stargazers_count"]
    h["url"] = d.get("html_url") or f"https://github.com/{repo}"
    h["description"] = (d.get("description") or meta.get("description") or "")[:240]
    h["language"] = d.get("language") or ""
    h["created"] = (d.get("created_at") or "")[:10]
    h["s"] = dict(sorted(h["s"].items())[-120:])  # keep about four months
    ok += 1

hist["updated"] = today
json.dump(hist, open(hp, "w"), indent=0, separators=(",", ":"), ensure_ascii=False)
print(f"{today}: {ok} repos updated, {gone} gone, {len(hist['repos'])} in history")
