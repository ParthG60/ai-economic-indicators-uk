# How this was built

I built this with [Claude Code](https://www.anthropic.com/claude-code) as a pair-programmer, over a
series of sessions. I'm putting this log here because for an AI-economics project it would be odd to
hide the AI, and because the useful part of the story isn't the code the model wrote, it's the
decisions about what to measure and what to trust. Those stayed with me. A few that mattered:

## Catching a measure that was lying to me

The labour-market track started with a longitudinal "flows" chart: of the people entering AI-exposed
jobs, what share were new to the workforce. It produced a clean-looking number, around 3%, and I
nearly kept it. It felt too low, so I dug in. Two problems: the measure conflated genuine new entrants
with people switching jobs, and the longitudinal sample behind it was tiny, a few dozen people per
cell once you cut by age and exposure. A clean-looking number built on twelve observations is worse
than no number.

So I threw it out and switched to a **recent-hire** measure on the much larger cross-sectional file:
everyone with under a year at their employer, by exposure and age. That gave ~200 most-exposed hires
per quarter instead of dozens, and it answers the actual question (is the hiring gate narrowing for the
young?) more directly. The lesson I kept reaching for: prefer the large sample and the measure that
maps to the question, even when a fancier panel method looks more sophisticated.

## Stock versus flow, and resisting the causal story

The headcount in exposed jobs (the "stock") fell only modestly for the young; recent hiring into those
jobs fell sharply. The honest read is a hiring-door effect, not a firing-door one, and I built the
dashboard to show both views side by side so a reader can see the gap themselves.

The hardest call was a confounder. The most AI-exposed jobs are also the most home-workable, and once
you restrict to on-site young workers the whole decline disappears. The tempting move is to bury that.
I did the opposite and made it the fourth chart, because the overlap is real and not a coincidence: AI
has landed hardest on desk and knowledge work, which is exactly the work that can be done remotely. The
dashboard says, in plain terms, that an AI effect can't be cleanly separated from a remote-work one,
and that this is descriptive, not causal. That caveat is the most important sentence on the page.

## Tuning the macro track for the UK rather than cloning Stanford

The US and UK sit on opposite sides of the AI supply chain (the US builds it, the UK buys it), so a
blind clone of Stanford's twelve indicators would mismeasure the UK. I dropped indicators that need a
domestic electronics supply chain the UK lacks, and added computer-services imports, the cloud and
compute bought from abroad, which turns out to be the clearest UK takeoff signal. Domestic-capital
measures are flagged as structurally muted here for the same reason.

## Design and accessibility, including one I got wrong first

The charts use a colour-blind-safe palette. My first attempt at "make it accessible" added dashes and
markers and a toggle, which the brief rightly rejected as clutter. The correct fix was simpler: pick a
colour pair that differs in lightness as well as hue (dark blue vs orange, the Okabe-Ito two-class
pair), so the lines stay distinct even when colour vision is reduced. I verified it by running a
deuteranopia and protanopia simulation over a screenshot of the rendered page rather than trusting the
claim. Worth recording as a reminder that "accessible" has a testable definition.

## On reproducibility and the data

The microdata can't be redistributed (UK Data Service licence), so the repo ships the aggregated CSVs
and the scripts that produce them, plus instructions to regenerate from your own licensed copy. The
public macro series pull live from ONS, the Bank of England and DESNZ, with curated fallbacks so a
failed fetch never silently corrupts a chart.
