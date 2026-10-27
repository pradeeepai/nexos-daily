# The Nexos Daily

An AI-first morning paper, served at https://pradeeepai.github.io/nexos-daily/.

- `index.html` is the reader. It loads `editions/index.json` and one JSON file per edition.
- The reader also shows Trending repos (`#trending`), the Ecosystem tracker (`#tracker`), the Layoffs tracker (`#layoffs`) and the Week in review (`#week`) in the same page, without a reload. Data: `trending/`, `stars/`, `layoffs/tracker.json` and `weekly/`.
- A scheduled publisher adds `editions/YYYY-MM-DD.json` every morning at 8:00 am IST and updates `editions/index.json`.
- Stories are picked and summarised by AI desks. Every story links to its source.
