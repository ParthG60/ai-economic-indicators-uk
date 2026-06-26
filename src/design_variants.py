"""Design-direction explorer for the UK AI Economic Indicators dashboard.

Renders the SAME representative dashboard slice (header, stat cards, a section, a real
data chart, a callout, evidence chips, footer) in four distinct visual identities, so we
can judge which reads best for a UK economics institute. Each THEME is a token set
(typography + palette + shape); these tokens ARE the project style guide (see DESIGN.md).
Real Canaries data is used so the charts are honest, not lorem.

  whitepaper — warm-paper academic, serif display (our refined status quo / Stanford-DEL family)
  institute  — navy + teal on white, grotesk display (IFS / Resolution Foundation / AISI-light)
  lab        — dark mode, cyan-teal accent, geometric texture (UK AISI)
  civic      — flat black-on-white, functional accent (GOV.UK / ONS official)

Run: python src/design_variants.py  ->  dashboard/design-variants/*.html
"""
import os
from string import Template

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "dashboard", "design-variants")
os.makedirs(OUT, exist_ok=True)

# real young-worker (22-25) employment index, base 2022 Q4 = 100
YEARS = ["2021-09", "2022-03", "2022-06", "2022-09", "2022-12", "2023-03", "2023-06", "2023-09",
         "2023-12", "2024-03", "2024-06", "2024-09", "2024-12", "2025-03", "2025-06", "2025-09", "2025-12", "2026-03"]
Q5 = [106.7, 101.8, 101.4, 98.6, 100.0, 102.4, 100.2, 98.8, 92.4, 88.2, 87.2, 84.7, 86.5, 88.0, 87.8, 90.1, 91.0, 91.4]
Q1 = [91.9, 94.8, 96.7, 100.6, 100.0, 99.8, 98.5, 98.2, 96.3, 96.9, 97.2, 97.3, 99.5, 100.3, 100.1, 100.6, 102.1, 99.2]

THEMES = [
    dict(key="whitepaper", name="Whitepaper — warm academic",
         fonts="family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500",
         f_display='"Fraunces",Georgia,serif', f_body='"IBM Plex Sans",system-ui,sans-serif', f_mono='"IBM Plex Mono",monospace',
         bg="#f6f3ec", surface="#fffdf8", headbg="#f6f3ec", ink="#211f1b", muted="#6f6a5f", rule="#e6dfd1", grid="#ece6d8",
         accent="#1c4e80", accent_ink="#ffffff", s_q1="#3f7d57", s_q5="#b0402d", pos="#3f7d57", neg="#b0402d",
         radius="5px", cardbd="1px solid #e6dfd1", topbar="", texture="none", shadow="none",
         kick_ls=".24em", h1w="500", note_bd="3px solid #1c4e80"),
    dict(key="institute", name="Institute — navy + teal",
         fonts="family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,700&family=Hanken+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500",
         f_display='"Bricolage Grotesque",system-ui,sans-serif', f_body='"Hanken Grotesk",system-ui,sans-serif', f_mono='"IBM Plex Mono",monospace',
         bg="#f4f7f8", surface="#ffffff", headbg="#ffffff", ink="#0b1f33", muted="#5c6b78", rule="#dde6ea", grid="#eaf0f2",
         accent="#0e7c86", accent_ink="#ffffff", s_q1="#2b6a86", s_q5="#c0442f", pos="#0e7c86", neg="#c0442f",
         radius="11px", cardbd="1px solid #dde6ea", topbar="", texture="none", shadow="0 1px 2px rgba(11,31,51,.05)",
         kick_ls=".2em", h1w="700", note_bd="4px solid #0e7c86"),
    dict(key="lab", name="Lab — AISI dark",
         fonts="family=Schibsted+Grotesk:wght@400;600;700&family=Hanken+Grotesk:wght@400;500&family=JetBrains+Mono:wght@400;500",
         f_display='"Schibsted Grotesk",system-ui,sans-serif', f_body='"Hanken Grotesk",system-ui,sans-serif', f_mono='"JetBrains Mono",monospace',
         bg="#0e141a", surface="#161f29", headbg="#0e141a", ink="#e7eef4", muted="#8ea3b3", rule="#25333f", grid="#1d2a35",
         accent="#35d0c6", accent_ink="#06231f", s_q1="#6aa7ff", s_q5="#ff8a6b", pos="#4fd1a1", neg="#ff8a6b",
         radius="13px", cardbd="1px solid #25333f", topbar="",
         texture="radial-gradient(circle at 1px 1px, rgba(53,208,198,.10) 1px, transparent 0)", shadow="0 1px 0 rgba(255,255,255,.02)",
         kick_ls=".22em", h1w="700", note_bd="3px solid #35d0c6"),
    dict(key="civic", name="Civic — GOV.UK / ONS",
         fonts="family=Public+Sans:wght@400;600;700;800",
         f_display='"Public Sans",system-ui,sans-serif', f_body='"Public Sans",system-ui,sans-serif', f_mono='"Public Sans",system-ui,sans-serif',
         bg="#ffffff", surface="#ffffff", headbg="#ffffff", ink="#0b0c0c", muted="#505a5f", rule="#b1b4b6", grid="#e7eaeb",
         accent="#1d70b8", accent_ink="#ffffff", s_q1="#00703c", s_q5="#d4351c", pos="#00703c", neg="#d4351c",
         radius="0px", cardbd="1px solid #b1b4b6", topbar="#0b0c0c", texture="none", shadow="none",
         kick_ls=".1em", h1w="800", note_bd="5px solid #1d70b8"),
]


def chart_svg(t):
    """Hand-built SVG line chart of the real young-worker series, themed."""
    W, H, pl, pr, pt, pb = 600, 290, 6, 64, 16, 26
    lo, hi = 82, 108
    n = len(Q5)
    def X(i): return pl + i * (W - pl - pr) / (n - 1)
    def Y(v): return pt + (hi - v) / (hi - lo) * (H - pt - pb)
    def poly(s): return " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(s))
    base = Y(100)
    grids = "".join(f'<line x1="{pl}" x2="{W-pr}" y1="{Y(g):.1f}" y2="{Y(g):.1f}" stroke="{t["grid"]}" stroke-width="1"/>'
                    f'<text x="{W-pr+6}" y="{Y(g)+3:.1f}" font-size="10" fill="{t["muted"]}" font-family="{t["f_mono"]}">{g}</text>'
                    for g in (85, 90, 95, 100, 105))
    area = f'M{X(0):.1f},{base:.1f} L' + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(Q5)) + f' L{X(n-1):.1f},{base:.1f} Z'
    cg = X(4)
    ticks = "".join(f'<text x="{X(i):.1f}" y="{H-6}" font-size="10" fill="{t["muted"]}" font-family="{t["f_mono"]}" text-anchor="middle">{YEARS[i][:4]}</text>'
                    for i in (1, 5, 9, 13, 17))
    return f'''<svg viewBox="0 0 {W} {H}" width="100%" preserveAspectRatio="xMidYMid meet" role="img">
 {grids}
 <line x1="{pl}" x2="{W-pr}" y1="{base:.1f}" y2="{base:.1f}" stroke="{t["muted"]}" stroke-width="1" stroke-dasharray="4 3"/>
 <line x1="{cg:.1f}" x2="{cg:.1f}" y1="{pt}" y2="{H-pb}" stroke="{t["accent"]}" stroke-width="1" stroke-dasharray="2 3" opacity=".7"/>
 <text x="{cg+4:.1f}" y="{pt+10}" font-size="10" fill="{t["accent"]}" font-family="{t["f_mono"]}">ChatGPT</text>
 <path d="{area}" fill="{t["s_q5"]}" opacity=".10"/>
 <polyline points="{poly(Q1)}" fill="none" stroke="{t["s_q1"]}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>
 <polyline points="{poly(Q5)}" fill="none" stroke="{t["s_q5"]}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>
 <circle cx="{X(n-1):.1f}" cy="{Y(Q5[-1]):.1f}" r="3.4" fill="{t["s_q5"]}"/>
 <circle cx="{X(n-1):.1f}" cy="{Y(Q1[-1]):.1f}" r="3.4" fill="{t["s_q1"]}"/>
 {ticks}
</svg>'''


CSS = Template("""
*{box-sizing:border-box} html{scroll-behavior:smooth}
body{font-family:$f_body;margin:0;background:$bg;color:$ink;-webkit-font-smoothing:antialiased;line-height:1.55;font-size:15px}
.wrap{max-width:1080px;margin:0 auto;padding:0 30px}
.serif{font-family:$f_display} .mono{font-family:$f_mono}
.topbar{height:8px;background:$topbar}
header{background:$headbg;padding:54px 0 0;border-bottom:1px solid $rule;background-image:$texture;background-size:22px 22px}
.kicker{font-family:$f_mono;font-size:11.5px;letter-spacing:$kick_ls;text-transform:uppercase;color:$accent;margin:0 0 16px}
h1{font-family:$f_display;font-weight:$h1w;font-size:clamp(34px,5.4vw,52px);line-height:1.03;letter-spacing:-.5px;margin:0;max-width:17ch;color:$ink}
.lede{font-size:18px;color:$muted;max-width:60ch;margin:20px 0 0}
.meta{font-family:$f_mono;font-size:11px;letter-spacing:.04em;color:$muted;margin:24px 0 30px;display:flex;gap:8px 22px;flex-wrap:wrap;align-items:center}
.dot{width:7px;height:7px;border-radius:50%;background:$pos;display:inline-block;margin-right:7px}
main{padding:46px 0 70px}
.eyebrow{font-family:$f_mono;font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;color:$accent;margin:0 0 11px}
h2{font-family:$f_display;font-weight:$h1w;font-size:clamp(25px,3.4vw,33px);letter-spacing:-.3px;margin:0 0 8px;color:$ink}
.sub{color:$muted;font-size:15px;margin:8px 0 24px;max-width:74ch}
.sub b{color:$ink}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:6px 0 30px}
.card{background:$surface;border:$cardbd;border-radius:$radius;padding:18px 20px;box-shadow:$shadow}
.cval{font-family:$f_mono;font-size:31px;font-weight:600;letter-spacing:-1px;line-height:1}
.cval.pos{color:$pos} .cval.neg{color:$neg}
.clab{font-size:13px;font-weight:600;margin-top:10px;color:$ink}
.csub{font-size:11.5px;color:$muted;margin-top:3px}
.chart{background:$surface;border:$cardbd;border-radius:$radius;padding:16px 18px;box-shadow:$shadow;margin:0 0 22px}
.chart-t{font-family:$f_display;font-size:17px;font-weight:$h1w;color:$ink;margin:0 0 2px}
.chart-s{font-size:12px;color:$muted;margin:0 0 10px}
.leg{display:flex;gap:18px;font-size:12.5px;color:$muted;margin-top:6px;font-family:$f_mono}
.sw{display:inline-block;width:14px;height:3px;border-radius:2px;vertical-align:3px;margin-right:6px}
.note{background:$surface;border:$cardbd;border-left:$note_bd;border-radius:$radius;padding:15px 18px;font-size:13.5px;color:$muted;margin:0 0 24px;max-width:90ch}
.note b{color:$ink}
.chips{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;font-size:12.5px;color:$muted;margin:0 0 8px;font-family:$f_mono}
.chip{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:7px;vertical-align:-1px}
footer{border-top:1px solid $rule;padding:26px 0 60px;color:$muted;font-size:12px;font-family:$f_mono;line-height:1.7}
a{color:$accent}
@media(max-width:700px){.wrap{padding:0 18px}.cards{grid-template-columns:1fr 1fr}}
""")

BODY = Template("""
<div class='topbar'></div>
<header><div class='wrap'>
 <p class='kicker'>UK Economic Measurement &middot; after Stanford Digital Economy Lab</p>
 <h1>UK AI Economic Indicators</h1>
 <p class='lede'>Is AI being adopted, transforming the macroeconomy, and reshaping the labour market in Britain? Three tracks, built from live UK public data.</p>
 <div class='meta'><span><span class='dot'></span>LIVE &middot; ONS &middot; Bank of England &middot; DESNZ &middot; Nomis &middot; Ofcom</span><span>UK replication</span></div>
</div></header>
<main><div class='wrap'>
 <div class='eyebrow'>03 &mdash; Labour market</div>
 <h2>The canaries: AI-exposed jobs</h2>
 <p class='sub'>Employment by <b>age &times; AI-exposure</b>, cut from Labour Force Survey microdata. The headline: young workers in the most-exposed jobs are losing ground, but the signal turns on working-from-home.</p>
 <div class='cards'>
  <div class='card'><div class='cval neg'>&minus;8.6%</div><div class='clab'>Young in most-exposed jobs</div><div class='csub'>age 22&ndash;25 &middot; employment vs 2022 Q4</div></div>
  <div class='card'><div class='cval pos'>+5.0%</div><div class='clab'>On-site young, exposed</div><div class='csub'>decline is remote-only</div></div>
  <div class='card'><div class='cval neg'>&minus;8.2%</div><div class='clab'>Automation-type, young</div><div class='csub'>AI does the task &middot; trough &minus;33%</div></div>
  <div class='card'><div class='cval pos'>+5.7%</div><div class='clab'>Augmentation-type, young</div><div class='csub'>AI assists the worker</div></div>
 </div>
 <div class='chart'>
  <p class='chart-t'>Young workers (22&ndash;25): employment by AI-exposure</p>
  <p class='chart-s'>Index, 2022 Q4 = 100 &middot; 4-quarter rolling</p>
  $svg
  <div class='leg'><span><span class='sw' style='background:$s_q5'></span>Most-exposed (Q5)</span><span><span class='sw' style='background:$s_q1'></span>Least-exposed (Q1)</span></div>
 </div>
 <div class='note'><b>How to read this.</b> The most-exposed jobs are also the home-workable ones (Q5 ~39% mainly-WFH vs Q1 ~5%). Restrict to on-site young workers and the decline disappears, so the clean &ldquo;AI is cutting entry-level jobs&rdquo; story is real in the raw cut but materially qualified once you account for working-from-home.</div>
 <div class='chips'>
  <span><span class='chip' style='background:$neg'></span>Strong</span>
  <span><span class='chip' style='background:$accent'></span>Mild</span>
  <span><span class='chip' style='background:$muted'></span>Neutral</span>
  <span><span class='chip' style='background:$s_q1'></span>Contradictory</span>
 </div>
</div></main>
<footer><div class='wrap'>Sources &mdash; ONS &middot; Bank of England &middot; DESNZ &middot; Ofcom &middot; Anthropic Economic Index. &nbsp;Design direction: <b>$name</b>.</div></footer>
""")

PAGE = Template("""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>AIEI &mdash; $name</title>
<link rel='preconnect' href='https://fonts.googleapis.com'><link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>
<link href='https://fonts.googleapis.com/css2?$fonts&display=swap' rel='stylesheet'>
<style>$css</style></head><body>$body</body></html>""")

for t in THEMES:
    css = CSS.substitute(t)
    body = BODY.substitute(t, svg=chart_svg(t))
    html = PAGE.substitute(name=t["name"], fonts=t["fonts"], css=css, body=body)
    path = os.path.join(OUT, f"{t['key']}.html")
    open(path, "w", encoding="utf-8").write(html)
    print("wrote", path)
print(f"\n{len(THEMES)} design variants -> {OUT}")
