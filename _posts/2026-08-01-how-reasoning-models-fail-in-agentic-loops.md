---
layout: default
title: "Hops, Skips, and Spirals: How Reasoning Models Fail and Why It Compounds in Agent Loops"
date: 2026-08-01
excerpt: "Reasoning models don't fail randomly, they fail in patterns: missed hops, coverage gaps, misread questions, and overthinking spirals. A single wrong answer is forgiving; an agent loop that plans, acts, and re-plans is not. This post walks through the common failure patterns and why they compound once you put a reasoning model inside an agentic loop."
---

# {{ page.title }}

*Posted {{ page.date | date: "%B %d, %Y" }}*

***Views are my own***

## TL;DR

Reasoning models are designed to "think" in long chains before answering, but they don't fail randomly. They fail in **recognizable patterns**: they skip evidence
they were supposed to combine, they answer before they've covered the question,
they misread what was asked in the first place, and they *overthink*, spending
5–20× the compute re-checking answers they already had. On a single benchmark
question, a plain accuracy score hides all of this. But the moment you drop the
same model into an **agentic loop**, plan, act (use tools for actions), observe, re-plan, repeat, each
hidden failure becomes the input to the next step, and small per-step errors
**compound** into large trajectory failures. This post draws on two pieces of
work: our own diagnosis of multi-hop reasoning failures [1], and a structural
analysis of *why* models overthink [2].

---

## Why a single answer is forgiving and a loop is not

Most of how we evaluate reasoning models still assumes a one-shot world: ask a
question, grade the answer, move on. Basically assess a user query and final response pair. If the model wandered for ten paragraphs
and still landed on the right token, it scores the same as a model that got
there cleanly.

Agents break that assumption - an agent doesn't produce *an answer*, it produces
a **trajectory**: it reads context, decides an action, calls a tool, observes
the result, and reasons again until it reaches a happy medium. Every intermediate reasoning step is load-bearing
because the *next* step is conditioned on it (feels very bayesian for sure). A subtle error that would have been
invisible in a one-shot score now silently steers the rest of the run.

That is the whole reason the failure *patterns* below matter more than the
headline accuracy number.

---

## Pattern 1: There are missed hops and coverage gaps

In our work on multi-hop analysis [1], we looked at questions that can only be
answered by **combining evidence from multiple distinct sources**, the kind of
"hop from A to B to C" reasoning that real tasks constantly require. We
categorized failures along dimensions that plain accuracy collapses:

- **Missed hops**: the model integrates *some* of the required grounding data sources but not
  all of them. It looks like reasoning; it's actually a shortcut that skipped a
  link in the chain.
- **Coverage gaps**: the model stops gathering evidence before it has everything
  the question needs, then answers from a partial picture.

Both look fine in isolation and can even produce a plausible-sounding answer.

**Why it compounds in a loop:** an agent that skipped a hop doesn't just return a
slightly-wrong answer, it takes an *action* on partial evidence (files the
wrong ticket, queries the wrong record, emails the wrong person). The next
observation is now off-distribution, and the model reasons forward from a state
the task never should have reached.

---

## Pattern 2: Overthinking - Explorer and Late Landing

The counterintuitive failure is the opposite of laziness. Reasoning models often
*over*-reason. The ACL 2026 analysis in [2] introduces **TRACE**, which breaks a
model's chain of thought into minimal "sub-thoughts" and reconstructs the logical
graph, exposing *when* the extra thinking stops being useful. It finds two
dominant shapes:

- **Explorer**: the reasoning model keeps exploring branches it doesn't need, well past the
  point where the answer was reachable (over-exploration).
- **Late Landing**: the reasoning model *has* the answer, then keeps re-verifying and
  cross-checking it (over-verification).

The striking number: on simple queries this can cost **5–20× more compute with no
accuracy benefit** [2]. Crucially, [2] reframes overthinking with a
**utility-based** definition — reasoning is only "useful" if it raises the
probability of a correct or more robust answer, not merely if it looks thorough.
This lines up with what we saw in [1]: overthinking wasn't harmless verbosity —
the extra steps introduced *new* factual and logical errors.

**Why it compounds in a loop:** overthinking is not just a latency and cost tax
(though in a multi-step agent, a 10× per-step tax is brutal). Over-exploration
gives the model more chances to talk itself *out* of a correct intermediate
conclusion, and Late-Landing verification spirals can flip a right answer to a
wrong one right before the agent commits an action.

---

## Pattern 3: Misreading the question before reasoning even starts

The most upstream failure in [1] is the quietest: the model **misinterprets the
question before the reasoning process begins**. No amount of careful chain-of-
thought rescues a run that started by solving the wrong problem, the reasoning
is often internally coherent/correct, but just pointed in the wrong direction because of question misinterpretation.

**Why it compounds in a loop:** a misframed goal is the worst possible seed for an
agent, because every subsequent plan, tool call, and observation is faithfully
optimizing the wrong objective. The trajectory can look confident and competent
end-to-end and still be entirely off-target. The cost is very high in these cases, as the model will not stop until a response is generated.

---

## The compounding effect, concretely

Here's the intuition that makes all of this urgent for agents. Suppose each step
of a loop is independently "good" with probability *p*. The probability that an
*n*-step trajectory is clean is roughly *pⁿ*:

| Per-step reliability | 3 steps | 5 steps | 10 steps | 20 steps |
|---|---|---|---|---|
| 99% | 97% | 95% | 90% | 82% |
| 95% | 86% | 77% | 60% | 36% |
| 90% | 73% | 59% | 35% | 12% |

A model that feels "95% reliable" on one-shot questions is a coin flip over a
ten-step task and worse than a coin flip over twenty. And the failure patterns
above are exactly the ones that *aren't* independent, a missed hop or a misread
question makes the *next* step more likely to fail too, so real trajectories
often decay faster than this optimistic table suggests.

![Chance a full agent trajectory stays clean as the number of steps grows, for 90%, 95%, and 99% per-step reliability. Even 95% reliability drops below a coin flip past ~13 steps.](/images/agentic-reliability-decay.png)

---

## What to measure? and what to do?

If the patterns are structural, the fixes should be too:

1. **Evaluate the trajectory, not just the answer.** Score planning quality, hop
   coverage, tool use, recovery, and end-state correctness — not only the final
   token. A right answer reached through a broken process is a latent failure.
2. **Check hops and coverage explicitly.** Before an agent acts, ask whether every
   required source was actually integrated and whether evidence coverage is
   complete — the two failure axes from [1].
3. **Budget verification with utility, not length.** Use the utility framing from
   [2]: stop reasoning when additional thought stops raising the probability of a
   better answer. Cap Explorer branches and Late-Landing re-checks.
4. **Guard the front door.** Because a misread question poisons everything
   downstream, validate the interpreted goal *before* the loop spends steps on it.

---

## Closing thought

These patterns aren't hypothetical, they've already surfaced in production. In
July 2025, a Replit coding agent deleted a live production database *during an
explicit code freeze*, then generated misleading explanations about what it had
done [3], a case of acting on a misread goal (misinterpreted question) and compounding it over
subsequent steps. Around the same time, Cursor's AI support bot invented a
non-existent "one device per subscription" policy and stated it as fact, which
triggered a wave of user cancellations before the company clarified it was a
hallucination [4]. And in a 2024 ruling that set an early precedent, a Canadian
tribunal held Air Canada liable after its chatbot confidently fabricated a
bereavement-fare refund policy [5]. Each of these is the same story the research
tells: a confident, plausible trajectory built on a hidden reasoning failure,
and no accuracy number would have flagged it in advance.

Reasoning models are getting better at *thinking*, but "more thinking" is not the
same as "better outcomes", sometimes it is the failure itself. As we move from
one-shot assistants to persistent agents that plan and act over many steps, the
patterns that a single accuracy number hides, the skipped hops, thin coverage,
misread goals, and overthinking spirals are exactly the ones that decide
whether the whole trajectory succeeds. Diagnosing *how* models fumble [1] and
understanding the *structure* of their overthinking [2] is how we build agents
that are reliable over the long haul, not just lucky on the last token.

---

## References

1. A. Yadav, I. Nalawade, S. Pillarichety, Y. Babu, **R. Ghosh**, S. Basu, W. Zhao,
   A. Nasaeh, S. Balasubramanian, S. Srinivasan. *Hop, Skip, and Overthink:
   Diagnosing Why Reasoning Models Fumble during Multi-Hop Analysis.*
   arXiv:2508.04699. [https://arxiv.org/abs/2508.04699](https://arxiv.org/abs/2508.04699)
2. X. F. Zhang, A. Mohananey, A. Chronopoulou, P. Papalampidi, S. Gupta,
   T. Munkhdalai, L. Wang, S. Upadhyay. *Do LLMs Really Need 10+ Thoughts for
   "Find the Time 1000 Days Later"? Towards Structural Understanding of LLM
   Overthinking.* ACL 2026 (Long Papers).
   [https://aclanthology.org/2026.acl-long.773/](https://aclanthology.org/2026.acl-long.773/)
3. Replit AI agent deletes production database during a code freeze (July 2025),
   as recounted by J. Lemkin / SaaStr.
   [https://www.saastr.com/replit-ai-agent-deleted-production-database/](https://www.saastr.com/replit-ai-agent-deleted-production-database/)
4. Cursor's AI support bot invents a fake subscription policy (April 2025),
   Ars Technica.
   [https://arstechnica.com/ai/2025/04/ai-support-bot-invents-nonexistent-policy-and-triggers-user-uproar/](https://arstechnica.com/ai/2025/04/ai-support-bot-invents-nonexistent-policy-and-triggers-user-uproar/)
5. *Moffatt v. Air Canada*, 2024 BCCRT 149 — airline held liable for its
   chatbot's fabricated refund policy.
   [https://www.canlii.org/en/bc/bccrt/doc/2024/2024bccrt149/2024bccrt149.html](https://www.canlii.org/en/bc/bccrt/doc/2024/2024bccrt149/2024bccrt149.html)
