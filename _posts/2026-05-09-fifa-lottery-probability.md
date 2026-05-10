---
layout: default
title: "What were my odds? Estimating FIFA 2026 ticket lottery chances probabilistically"
date: 2026-05-09
excerpt: "I applied for 2 tickets in the FIFA Random Selection Draw and won 1. This post walks through a transparent probability model — and an interactive page where you can play with the assumptions yourself."
---

# {{ page.title }}

*Posted {{ page.date | date: "%B %d, %Y" }}*

In the first week of January 2026 I applied for two tickets in the FIFA World Cup 2026 Random Selection Draw. I won the application for **Match 5 (Haiti vs. Scotland)** and lost the application for **Match 97 (a quarterfinal)**. After the draw closed I started wondering: *what were my actual odds, given how lopsided the demand was across matches?*

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
| Stadium capacity | FIFA published | Fixed (Gillette: 65,878) |
| Public-pool fraction | Industry rule of thumb | Prior centered at 65%, with uncertainty |
| Pre-sale drainage | FIFA: "nearly 2M tickets sold before phase 3" | Prior centered at 20% drainage of T_cat |
| Category supply share | Logical (Cat 3 is the largest tier) | Prior centered at 35% |
| Category demand share | Cheap-tier demand rises with match popularity (downgrade behaviour) | Interpolates 40% (low-demand) → 55% (high-demand) |
| Per-match demand | Unpublished — bucketed using "1M+ for 77 matches" | M5 lognormal at 800k; M97 lognormal at 5M |
| Global demand sum | FIFA: 500M+ across 104 matches | Per-iteration rescaling enforces Σ ≈ 500M ± 5% |
| q-rule | Unspecified by FIFA | Toggle between linear-in-q and application-equal |

The biggest source of uncertainty is per-match demand. The choice of lognormal priors with wide variance is deliberate — I want the credible intervals to reflect that I genuinely don't know the demand for any specific match.

## Why M5 and M97 are roughly independent

I applied for one ticket per match, two total. The 40-ticket aggregate cap doesn't bind here, so I can treat the two draws as independent. (If you'd applied for many tickets across many matches, you'd want a sequential-draw correction — at the cap, your earlier wins reduce your remaining lottery participation.)

## Results

Pulling the priors together and running 10,000 Monte Carlo draws under the central scenario:

- **Match 5 (Haiti vs. Scotland)**: median P(win) ≈ **2.5–3%**, 90% CI roughly [1.2%, 5%]
- **Match 97 (Quarterfinal)**: median P(win) ≈ **0.35–0.5%**, 90% CI roughly [0.15%, 0.9%]

So winning M5 and losing M97 sits comfortably inside the model's bulk — the second-most-likely joint outcome under the central settings. The model isn't refuted, and with N=2 it's also not strongly confirmed.

The interesting comparative result is the **demand × public-pool heatmap**: P(win) is much more sensitive to per-match demand than to the public-pool fraction. If you knew M97's true demand to within ±20%, you could collapse the credible interval substantially. Whereas tightening your prior on the public-pool fraction barely moves the needle.

## What v2 fixed (after a critique)

A first version of this model gave noticeably more optimistic numbers (M5 ~3.7%, M97 ~0.6%). After someone walked through the assumptions carefully, I rewrote it with four fixes:

1. **Pre-sale drainage** — Visa Presale and the Early Draw had moved ~2M tickets before the Random Selection Draw. The original model treated T_cat as fully available; v2 subtracts a 20% drainage prior.
2. **Global 500M demand constraint** — FIFA's reported aggregate is now enforced. Per Monte Carlo iteration, the sampled per-match demands are rescaled so the implied 104-match total respects 500M ± 5%. This forces the priors to be internally consistent in a way v1 didn't.
3. **Demand-share covariance** — A flat 45% Cat 3 demand share was the wrong simplification. Marquee matches see disproportionate downgrade-to-Cat-3 behavior, so v2 interpolates between 40% (low-demand) and 55% (high-demand).
4. **q-rule toggle** — v1 silently assumed P(win) ∝ q. The competing model is "each application is one entry regardless of tickets requested." For my q=1 applications this is a no-op, but the spread for multi-ticket apps is up to 4×, so v2 exposes it explicitly.

Net effect: numbers came down, credible intervals tightened, and the page now carries an [assumptions inventory](/fifa-lottery/#) (collapsed under the limitations section) listing every modeling choice — supply, demand, lottery mechanics, calibration anchors, and what's still open. That last bit matters more than the headline number; you should be able to push back on any single assumption and see the model react.

## Why I built it three ways

I put three deployable versions of this in the [source repo](https://github.com/reshmighosh/fifa-lottery-model):

1. **Marimo notebook** — live Python in the browser via WASM. Maximum interactivity (sliders re-run the actual simulation), but the bundle is ~30 MB.
2. **Quarto + Plotly** — pre-computed grid of scenarios rendered as interactive charts. ~3 MB. No live re-compute.
3. **Vanilla HTML + Plotly.js** — model formula reimplemented in JS, Monte Carlo runs on page load. ~3 MB, single file, instant load. *This is what's deployed [here](/fifa-lottery/).*

For a one-shot post like this, the simple HTML version was clearly the right call: zero build step, no Pyodide cold start, and the math is simple enough to port to JS without losing fidelity. The Marimo version is what I'd reach for if I were iterating on the model itself.

## What this isn't

This is not a calibration of FIFA's actual draw mechanism — they almost certainly stratify by category, residency, and possibly host-country bias in ways that aren't public. It's a transparent first-principles estimate that anchors on the two aggregate numbers FIFA *did* publish, and exposes every assumption as a slider.

## Next steps

The single biggest unknown in this model is per-match demand. **If FIFA publishes post-tournament attendance and sales-by-match data — should any of that become public — the natural next step is a proper Bayesian update.** Sample the prior, compute the likelihood from observed sell-through, post the updated probability. That'll meaningfully tighten the credible intervals and may force a real shift on the central estimates if FIFA's released numbers diverge from these priors. I'll write that follow-up the moment the data lands.

A few smaller follow-ups in the meantime:

- **Fraud / bot discount on reported demand** — if "effective" demand is 70–90% of the 500M+ headline, P(win) values are systematically low by ~10–40%.
- **Stage-aware supply shares** — knockout matches likely shift inventory toward Cat 1/2; v2 still uses one supply share for everything.
- **Portfolio-aware allocation** — FIFA's actual algorithm probably isn't fully independent across matches for an applicant. Heavy applicants likely get a conditional uplift on later matches if they got nothing earlier; doesn't matter for my N=2 case but matters for generalization.

## Try it

**[→ Interactive page](/fifa-lottery/)** — drag the sliders, watch the credible interval update.

**[→ Source on GitHub](https://github.com/reshmighosh/fifa-lottery-model)** — Marimo, Quarto, and HTML versions, plus the README explaining the deployment tradeoffs.

If you applied to the same draw and want to compare numbers, I'd love to hear from you — find me on [LinkedIn](https://www.linkedin.com/in/reshmi-ghosh/) or [Twitter](https://twitter.com/reshmigh).

— Reshmi
