"""Layoffs tracker data: layoffs/tracker.json in the site repo.
usage as a module: merge_items(repo, items, day) adds Layoffs desk items (deduplicated).
usage as a script:  python3 layoffs.py REPO seed.json [extra.json ...]  (rebuild from seed files + all past editions)
"""
import json, os, re, sys, glob, datetime

IND_BY_CO = {"microsoft": "Big Tech", "amazon": "Big Tech", "meta": "Big Tech", "google": "Big Tech", "apple": "Big Tech",
             "netflix": "Big Tech", "electronic arts": "Gaming", "qualcomm": "Semiconductors", "intel": "Semiconductors",
             "ebay": "Online marketplaces", "automattic": "Other tech", "oracle": "Enterprise software", "salesforce": "Enterprise software",
             "tcs": "IT services", "infosys": "IT services", "wipro": "IT services", "hcltech": "IT services", "tech mahindra": "IT services"}
ALIAS = {"ea": "electronic arts", "aws": "amazon", "google deepmind": "google", "alphabet": "google", "x": "twitter"}


def _co(s):
    c = re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()
    return ALIAS.get(c, c)


def _num(s):
    q = r"(?:about|around|roughly|nearly|some|up to|over|more than|approximately)?\s*"
    m = re.search(r"(?:cut|cuts|cutting|lay off|lays off|laying off|eliminate|eliminates|axe|axes|slash|slashes|trim|trims)\s+" + q + r"(\d[\d,]*)", s, re.I) \
        or re.search(r"(\d[\d,]*)\s+(?:jobs|layoffs|job cuts|roles|positions)\b", s, re.I)
    return int(m.group(1).replace(",", "")) if m else None


def _pct(s):
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", s, re.I)
    return float(m.group(1)) if m else None


def company_from_title(t):
    m = re.match(r"(.+?)\s+(?:cuts|to cut|offers|lays|lay|starts|plans|begins|confirms|announces|will|slashes|trims|eliminates|axes|shuts|closes|files)\b", t)
    return (m.group(1) if m else t.split()[0]).strip()


def entry_from_item(it, day):
    text = f"{it.get('title', '')}. {it.get('body', '')}"
    company = (it.get("company") or company_from_title(it.get("title", ""))).strip()
    count = it.get("count") if isinstance(it.get("count"), int) else _num(text)
    pct = it.get("pct") if isinstance(it.get("pct"), (int, float)) else _pct(text)
    kind = it.get("kind") or ("buyout" if re.search(r"buyout|voluntary", it.get("title", ""), re.I) else "layoff")
    return {"date": it.get("date") or day, "company": company, "count": count, "count_text": "", "pct": pct,
            "location": it.get("location", ""), "country": it.get("country", ""),
            "industry": it.get("industry") or IND_BY_CO.get(_co(company), ""), "kind": kind,
            "confirmed": it.get("confirmed", True), "source": str(it.get("source", "")).split("·")[0].strip(), "url": it.get("url", "")}


def _close(a, b, days=6):
    try:
        da, db = datetime.date.fromisoformat(a), datetime.date.fromisoformat(b)
        return abs((da - db).days) <= days
    except Exception:
        return a == b


def merge(entries, new):
    for e in entries:
        if _co(e["company"]) == _co(new["company"]) and _close(e["date"], new["date"]):
            for k in ("count", "pct", "industry", "country", "location"):
                if not e.get(k) and new.get(k):
                    e[k] = new[k]
            return False
    entries.append(new)
    return True


def load(repo):
    p = f"{repo}/layoffs/tracker.json"
    return json.load(open(p)) if os.path.exists(p) else {"entries": []}


def save(repo, data):
    os.makedirs(f"{repo}/layoffs", exist_ok=True)
    data["entries"].sort(key=lambda e: (e["date"], e["company"]), reverse=True)
    data["updated"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    s = json.dumps(data, indent=1, ensure_ascii=False)
    assert not re.search(r"Pradeep|your feed|wedding", s, re.I)
    open(f"{repo}/layoffs/tracker.json", "w").write(s)


def merge_items(repo, items, day):
    data = load(repo)
    n = sum(merge(data["entries"], entry_from_item(it, day)) for it in items)
    save(repo, data)
    return n


if __name__ == "__main__":
    repo, seeds = sys.argv[1], sys.argv[2:]
    data = {"entries": []}
    for s in seeds:
        for e in json.load(open(s)):
            merge(data["entries"], e)
    for f in sorted(glob.glob(f"{repo}/editions/20*.json")):
        ed = json.load(open(f))
        sec = ed.get("sections", {}).get("layoffs")
        for it in (sec or {}).get("items", []):
            merge(data["entries"], entry_from_item(it, ed["date"]))
    save(repo, data)
    print(len(data["entries"]), "entries")
