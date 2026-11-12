# usage: python3 apply_paper.py  -> regenerates paper.css and inlines it into index.html (safe to run again)
import os, re, subprocess, sys
D = os.path.dirname(os.path.abspath(__file__))
R = os.path.dirname(os.path.dirname(D))
subprocess.run([sys.executable, f"{D}/gen_paper.py"], check=True)
css = open(f"{D}/paper.css").read()
p = f"{R}/index.html"
s = open(p).read()

def rep(a, b):
    global s
    if b in s:
        return
    assert s.count(a) == 1, (a[:80], s.count(a))
    s = s.replace(a, b)

# fonts
rep("&family=JetBrains+Mono:wght@400;500&display=swap",
    "&family=JetBrains+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&family=Figtree:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap")
# pre-paint
rep('(s==="minimal"||s==="unslop")?s:"magazine"', '(s==="minimal"||s==="unslop"||s==="paper")?s:"magazine"')
# settings and the Aa button
rep('<button type="button" data-v="unslop">Unslop</button></div>', '<button type="button" data-v="unslop">Unslop</button><button type="button" data-v="paper">Paper</button></div>')
rep('title="Switch design: Magazine, Minimal, Unslop"', 'title="Switch design: Magazine, Minimal, Unslop, Paper"')
rep('["minimal", "unslop"].includes(store.get("nx-style"))', '["minimal", "unslop", "paper"].includes(store.get("nx-style"))')
rep('const o = ["magazine", "minimal", "unslop"];', 'const o = ["magazine", "minimal", "unslop", "paper"];')
# css block between markers
block = "/*PAPER:START*/\n" + css + "/*PAPER:END*/\n"
if "/*PAPER:START*/" in s:
    s = re.sub(r"/\*PAPER:START\*/.*?/\*PAPER:END\*/\n", lambda m: block, s, flags=re.S)
else:
    assert s.count("</style>\n</head>") == 1
    s = s.replace("</style>\n</head>", block + "</style>\n</head>")
open(p, "w").write(s)
print("index.html patched")
