---
layout: default
title: "What were my odds? Estimating FIFA 2026 ticket lottery chances probabilistically"
date: 2026-05-09
excerpt: "I applied for 2 tickets in the FIFA Random Selection Draw and won 1. This post walks through a transparent probability model — and an interactive page where you can play with the assumptions yourself."
---

# {{ page.title }}

*Posted {{ page.date | date: "%B %d, %Y" }}*

In December 2025 I applied for two tickets in the FIFA World Cup 2026 Random Selection Draw. I won the application for **Match 5 (Haiti vs. Scotland)** and lost the application for **Match 97 (a quarterfinal)**. After the draw closed I started wondering: *what were my actual odds, given how lopsided the demand was across matches?*

FIFA published two useful aggregate numbers and almost nothing else:

- [500M+ total ticket requests](https://inside.fifa.com/organisation/media-releases/over-500-million-ticket-requests-world-cup-2026-random-selection-draw) across 104 matches
- [77 of those matches received 1M+ requests each](https://www.wfaa.com/article/sports/soccer/world-cup/world-cup-2026-tickets-demand/287-084c28e3-f059-44a5-a00e-7003e58bf257)

Per-match counts were never released. So the modeling problem is: given those aggregates and a few well-defined unknowns, can we put a credible interval on the probability of winning a specific application? Yes — and you don't need anything more sophisticated than a Monte Carlo over informed priors.

> **[→ Try the interactive version](/fifa-lottery/)** — sliders for demand, supply share, and public-pool fraction; the point estimate updates live, and the histogram shows the full posterior over 10,000 simulated draws.

## The model in one line

For a single application:

```
P(win) ≈ q × T_cat / D_cat
```

where

- `q` is the number of tickets requested (capped at 4 per match by FIFA),
- `T_cat` = stadium capacity × public-pool fraction × category supply share, and
- `D_cat` = total per-match demand × category demand share.

That's the whole thing. Everything interesting is in how you put priors on the four inputs.

## What's known vs. assumed

| Input | Source | How I treat it |
|---|---|---|
| Stadium capacity | FIFA published | Fixed (44k for M5, 82k for M97) |
| Public-pool fraction | Industry rule of thumb | Prior: ~60% of capacity, with uncertainty |
| Category supply share | Logical (Cat 3 is the largest tier) | Prior centered at 35% |
| Category demand share | Heuristic (cheapest non-host-restricted tier draws disproportionate demand) | Prior centered at 45% |
| Per-match demand | Unpublished — bucketed using "1M+ for 77 matches" | M5 below 1M (lognormal at 400k); M97 above 1M (QF, lognormal at 2.5M) |

The biggest source of uncertainty is per-match demand. The choice of lognormal priors with quite wide variance is deliberate — I want the credible intervals to reflect that I genuinely don't know the demand for any specific match.

## Why M5 and M97 are roughly independent

I applied for one ticket per match, two total. The 40-ticket aggregate cap doesn't bind here, so I can treat the two draws as independent. (If you'd applied for many tickets across many matches, you'd want a sequential-draw correction — at the cap, your earlier wins reduce your remaining lottery participation.)

## Results

Pulling the priors together and running 10,000 Monte Carlo draws:

- **Match 5 (Haiti vs. Scotland)**: median P(win) ≈ **3.7%**, 90% CI ≈ [1.8%, 7.4%]
- **Match 97 (Quarterfinal)**: median P(win) ≈ **0.6%**, 90% CI ≈ [0.3%, 1.3%]

So winning the M5 application and losing the M97 application is *exactly* what the model would predict on average. The point estimate of "win 1 of these 2" is around 3.6% — not common, but very much in the meat of the distribution. No update needed.

The interesting result for me was the **demand × public-pool heatmap**: P(win) is much more sensitive to per-match demand than to the public-pool fraction. If you knew M97's true demand to within ±20%, you could collapse the credible interval substantially. Whereas tightening your prior on the public-pool fraction barely moves the needle.

## Why I built it three ways

I put three deployable versions of this in the [source repo](https://github.com/reshmighosh/fifa-lottery-model):

1. **Marimo notebook** — live Python in the browser via WASM. Maximum interactivity (sliders re-run the actual simulation), but the bundle is ~30 MB.
2. **Quarto + Plotly** — pre-computed grid of scenarios rendered as interactive charts. ~3 MB. No live re-compute.
3. **Vanilla HTML + Plotly.js** — model formula reimplemented in JS, Monte Carlo runs on page load. ~3 MB, single file, instant load. *This is what's deployed [here](/fifa-lottery/).*

For a one-shot post like this, the simple HTML version was clearly the right call: zero build step, no Pyodide cold start, and the math is simple enough to port to JS without losing fidelity. The Marimo version is what I'd reach for if I were iterating on the model itself.

## What this isn't

This is not a calibration of FIFA's actual draw mechanism — they almost certainly stratify by category, residency, and possibly host-country bias in ways that aren't public. It's a transparent first-principles estimate that anchors on the two aggregate numbers FIFA *did* publish, and exposes every assumption as a slider.

If FIFA publishes post-tournament attendance/sales by match, the natural next step is a Bayesian update: sample the prior, compute the likelihood from observed sell-through, post the updated probability. That'd be a good follow-up post.

## Try it

**[→ Interactive page](/fifa-lottery/)** — drag the sliders, watch the credible interval update.

**[→ Source on GitHub](https://github.com/reshmighosh/fifa-lottery-model)** — Marimo, Quarto, and HTML versions, plus the README explaining the deployment tradeoffs.

If you applied to the same draw and want to compare numbers, I'd love to hear from you — find me on [LinkedIn](https://www.linkedin.com/in/reshmi-ghosh/) or [Twitter](https://twitter.com/reshmigh).

— Reshmi
