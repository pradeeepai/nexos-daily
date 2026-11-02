# Publish scripts

The daily publish job runs these scripts. They live in the repo so that a fresh session can use them.

- `build.py DIGEST_DIR REPO DAY --ov overrides.json --brief briefing.txt` builds `editions/DAY.json`, `trending/DAY.json`, `stars/tracked.json` and `layoffs/tracker.json`.
- `week.py REPO picks.json` builds the Sunday Week in review (`weekly/`).
- `layoffs.py` merges Layoffs desk items into `layoffs/tracker.json`. `build.py` calls it.
