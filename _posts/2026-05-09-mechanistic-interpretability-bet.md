---
layout: default
title: "Why I bet on mechanistic interpretability"
date: 2026-05-09
excerpt: "Two years ago I made a deliberate bet to focus on mechanistic interpretability of language models. The thesis was simple: the shortest path to a better product is understanding why the model behaves the way it does. Here's what I worked on, what I learned, and where I think this goes next."
---

# {{ page.title }}

*Posted {{ page.date | date: "%B %d, %Y" }}*

A couple of years ago I made a deliberate bet on where to spend my research time, and increasingly my team's: **mechanistic interpretability of large language models**, with a specific focus on how production-class models actually use the information they're given. The thesis was simple, even if it doesn't sound like a hot take: **the shortest path to a better product is understanding why the model behaves the way it does — not making it bigger, not adding another loss term, not chasing another evaluation suite.** When you genuinely understand what's happening inside the model, you stop being surprised by it, you spot the gaps that benchmarks hide, and you ship features that hold up in production rather than fall apart at the user-experience layer.

This post is a stake in the ground on what that bet looked like in practice — what I worked on, what surprised me, and where I think the field needs to go next.

## What I mean by mechanistic interpretability

"Mechanistic interpretability" is a broad and broadening label. The narrow version — circuit-level analysis on small toy transformers — is intellectually beautiful, but it isn't where most of my time has gone. The flavor I've focused on is more applied: **probing real production-scale language models to understand which internal representations get used when, especially when the model has *both* parametric memory and retrieved context to draw from.**

That last clause is the whole game. Modern systems are not just LMs — they're LMs plus retrievers, plus tool calls, plus injected context, plus structured memory. Every shipped feature involves the model arbitrating between sources of information. If you can't see *which* sources the model is actually leaning on, you're flying blind.

## The papers, in narrative order

### *From RAGs to Rich Parameters* — [arXiv 2406.12824](https://arxiv.org/abs/2406.12824)

The question this paper asks is direct: when a language model is given retrieved context plus a query, **does it actually use the retrieved context, or does it fall back on what it learned during pre-training?** People had hand-waved about this for years, usually arguing one side or the other based on prompt-level tricks. We wanted a mechanistic answer.

We probed activations layer-by-layer and found that production-class LLMs lean *heavily* on retrieved context — they actively minimize their use of parametric memory when context is available. That sounds like unambiguous good news for RAG. It isn't. The same property that makes RAG work is the property that makes prompt injection work. The model is wired to defer to whatever you put in its context window; that's a feature for retrieval and a vulnerability for adversarial inputs. Once we understood the mechanism, it stopped being a surprise that prompt-injection defenses are so hard to get right by patching at the API layer alone.

### *Quantifying Reliance on External Information via Mechanistic Analysis* — BlackboxNLP @ EMNLP 2024, [arXiv 2410.00857](https://arxiv.org/abs/2410.00857)

The natural follow-up was: *by how much* does the model lean on context, and is that ratio stable across model families and knowledge types? We extended the methodology with activation patching to quantify the parametric-vs-context split, then asked when the lean reverses. Short answer: it isn't uniform. Specific layer ranges retain parametric bias for specific kinds of knowledge — and those are exactly the places worth focusing interpretability work if your goal is improving factual robustness.

This paper is the one I point people to when they ask "okay, but where would I actually intervene?" The probing maps tell you which layers to instrument, and where the upside lives.

### *On Surgical Fine-Tuning for Language Encoders* — EMNLP 2023 Findings, [arXiv 2310.17041](https://arxiv.org/abs/2310.17041)

The pre-cursor to the RAG line. Before I was probing models to understand RAG behavior, I was probing them to understand which *layers* actually need to move during task adaptation. The finding — that you can get most of the benefit of full fine-tuning by touching a small, principled subset of layers — was itself a small piece of interpretability. It told us layer-level locality matters, and that prepared the ground for the activation-patching work that came later.

### *Hop, Skip, and Overthink: Diagnosing Why Reasoning Models Fumble during Multi-Hop Analysis* — 2025

The newest line. Reasoning models are the hottest product surface right now, and they fail in ways that single-step generation doesn't. The interesting question isn't "do they hallucinate" (yes), it's "where in the multi-hop chain does the failure get introduced, and is it the same kind of failure each time?" Early findings: it isn't. The error modes cluster, and the clusters are tractable mechanistically. Expect more on this from us.

## What the bet has actually paid back

Every paper above was motivated by a problem my team or an adjacent team was running into in production:

- **Factual drift in RAG systems.** When retrieved context is stale or wrong, models parrot it. We now know mechanistically why: they're wired to. That changes how you build the retrieval layer, the monitoring layer, and the user-facing fallback behavior.
- **Prompt injection hidden in documents and images.** The same context-deference that makes RAG good makes it manipulable. Interpretability findings fed directly into how my team thinks about [prompt shields](https://www.theverge.com/2024/3/28/24114664/microsoft-safety-ai-prompt-injections-hallucinations-azure) and adversarial detection now.
- **Hallucination patterns.** Knowing which layers re-engage parametric memory tells you which interventions actually move the needle versus which are theater. Saves enormous amounts of dev cycles spent on things that won't generalize.
- **Knowing when to *not* ship a model.** This one is the underrated dividend. Interpretability evidence has, on multiple occasions, been the deciding factor for whether a model variant goes into production. Benchmarks tell you the average; mechanistic analysis tells you the tail.

## Where I think this goes next

Three directions I expect to spend time on (and would happily collaborate on) over the next 12–24 months:

1. **From probing to intervention.** Probing is descriptive. The next bar is *causal* — can we steer the parametric-vs-context tradeoff *at inference time*, per query, conditioned on context confidence? That's where this becomes a directly product-shaping tool rather than a postmortem one.
2. **Agentic and multi-step reasoning.** Single-turn RAG is a relatively clean mechanistic surface. Multi-step agents that loop tool calls, accumulate working memory, and replan over partial successes are where current interpretability methods break down — and where the most valuable next round of research sits.
3. **Interpretability that survives preference tuning.** Many of the cleanest probing results are on base models or supervised-fine-tuned models. The story gets messier after RLHF/DPO. Methodology that holds up *post* preference tuning is, in my opinion, the highest-leverage open problem in the area.

## Closing — the bet, restated

Picking interpretability as a research focus felt counter-trend when I started in 2023. The conventional view was that interpretability was either too academic to ship or too narrow to matter; the headline dollars were going elsewhere. I'm glad I made the bet anyway. Every product team I've worked alongside has eventually hit a wall that mechanistic understanding *resolved* — not a benchmark wall, but a "we don't know why this user-visible behavior keeps happening" wall. Interpretability is the cheapest tool I know for getting past that wall, and the dividend compounds with each model generation: the questions become more precise rather than less.

If you're working on related problems — especially the intervention, agent, or post-RLHF angles above — I'd love to compare notes. Find me on [LinkedIn](https://www.linkedin.com/in/reshmi-ghosh/) or [Twitter](https://twitter.com/reshmigh).

— Reshmi
