---
layout: default
title: "Remembering Is Not Enough: Evaluating Personalization and Memory Provenance"
date: 2026-10-26
excerpt: "Knowing whether personalization works is harder than checking whether an agent remembers a fact. We need to evaluate which conversational cues it selects, whether they are appropriate to reuse, and whether their provenance survives every summary and update."
---

# {{ page.title }}

*Posted {{ page.date | date: "%B %d, %Y" }}*

***Views are my own***

## TL;DR

It is not easy to evaluate memory. Knowing when personalization actually works
is harder than it looks, and with LLM-based assistants the problem gets bigger:
conversations grow, topics overlap, preferences change, and yesterday's useful
detail can become today's inappropriate assumption.

The question is not just **"Can the agent remember what I said?"** It is
**"Can it select the right cue, for this task, at this time, within an appropriate
privacy boundary, and show me where that cue came from?"**

That means evaluating more than recall. We need to separate factual memory,
useful personalization, appropriate reuse, and provenance. A correct memory can
still produce a bad personalized response. A citation can support a remembered
claim without proving that the claim influenced the answer. And sometimes the
best use of memory is choosing not to use it.

---

## 1. "It remembered me" is not an evaluation

Imagine asking an assistant to help write a project update. It remembers that
you prefer concise writing and produces a short draft.

That sounds like successful personalization. But several explanations fit:

- It used your earlier preference.
- It inferred brevity from the current request.
- It usually writes short project updates anyway.
- It retrieved a preference from a different context, where you had asked for
  short social posts, and happened to get lucky.

The final answer alone does not distinguish these cases.

Now imagine the assistant adds a personal detail from an earlier conversation.
The detail is accurate. The writing is fluent. The response is also something
you would never want to send to your colleagues.

Memory succeeded at recall and failed at judgment.

**Personalization is not the presence of remembered information. It is an
improvement in the current interaction because appropriate information was
used.** To evaluate that improvement, we need a comparison, not just an
impressive anecdote.

---

## 2. What recommender systems taught us, and where the analogy breaks

Earlier personalization systems often operated over a more bounded surface:
users, items, interaction histories, and a defined recommendation objective.
Items might have categories or topic representations; users might have explicit
ratings, implicit feedback, or learned preference embeddings. Not every system
was topic-based, and this was never a solved problem.

In fact, the recommender-systems literature has long recognized the importance
of context and the limits of a simple user-item formulation [1]. A preference
can depend on when, where, and why someone is making a choice.

Conversational assistants inherit those difficulties and loosen the boundaries.
There may be no fixed item catalog. The same assistant can help with code,
travel, research, writing, and a personal decision across an expanding history.
An agentic harness can add tool outputs and documents to that history, each with
different reliability and access constraints.

Even identifying a topic boundary is not straightforward. Topic segmentation
has a long research history: Hearst's TextTiling, for example, segments written
text into subtopic passages [2]. That is useful historical context, not evidence
that an algorithm for expository text solves conversational memory.

In conversation, a topic can disappear and return. A preference can span topics.
A sentence about another person can look like a statement about the user.
Something said while role-playing can look like a durable biographical fact.

Consider:

> "My sister is vegetarian. I am planning her birthday dinner. For my own meals,
> I usually eat fish."

Clustering this under *food preferences* is not enough. The assistant still
needs to preserve **who** each statement describes, **which task** it applies
to, and whether it is a lasting preference or temporary planning context.

The jump from topic segmentation to a ranked set of memory cues is substantial.
We are not just asking which passage resembles the current query. We are asking
which part of a previous interaction should be allowed to influence a new one.

---

## 3. A memory cue is a claim with conditions, not just a sentence

Here is a fictional example. These are illustrative conversations, not user data
or experimental results.

| Conversation | What was said | What should survive |
|---|---|---|
| January, planning a team dinner | "I'm vegetarian." | An explicit dietary statement, with its source and time |
| March, planning a family visit | "My father needs step-free access." | A task-relevant statement about the father, not the user |
| June, planning a trip | "I now eat fish, but not other meat." | An update that qualifies the earlier dietary statement |
| September, writing a conference abstract | "Please keep this under 150 words." | A local output constraint, not necessarily a permanent writing preference |

In October, the user asks:

> "Find a restaurant for my solo trip."

A useful system should consider the June update rather than blindly apply
January's statement. It should not turn the father's accessibility requirement
into a claim about the user. And it should not automatically apply September's
150-word constraint.

![Four fictional conversations on a timeline: the June dietary update is eligible for a solo restaurant request, while the January statement is superseded, the father's access requirement concerns the wrong subject, and the abstract limit is out of scope.]({{ '/images/memory/01_memory_timeline.svg' | relative_url }})

*Figure 1. Remembered correctly does not mean appropriate to reuse. This
illustrative timeline uses four conversations from the synthetic case study
below; it is not observed model behavior. [Open full-size figure]({{ '/images/memory/01_memory_timeline.svg' | relative_url }}).*

Importantly, the system should not silently replace *vegetarian* with a new
identity label the user never supplied. "Eats fish but no other meat" is closer
to the evidence than a confidently inferred profile.

This suggests a richer unit of memory:

- **Claim and subject:** what is asserted, and about whom?
- **Evidence:** which authorized source spans support it?
- **Epistemic status:** explicitly stated, inferred, or uncertain?
- **Scope:** a single request, a project, a relationship, or a broader preference?
- **Time:** when was it observed, and when does it apply?
- **Updates:** what qualifies, contradicts, or supersedes it?
- **Reuse constraints:** what retention and use are permitted in this context?

This is a proposed design checklist, not a standardized schema. More metadata
does not automatically make a system trustworthy. Its value is that it makes
assumptions inspectable and failures testable.

It also makes clear why recency alone is insufficient. A newer statement may
describe someone else, a hypothetical situation, or an exception.

---

## 4. What existing evaluations tell us, and what they do not

There is already useful work here. The point is not that memory and
personalization are unevaluated. It is that different benchmarks answer
different questions.

| Benchmark | What it evaluates | What that does not establish by itself |
|---|---|---|
| **LoCoMo** [3] | Long-term conversational memory through question answering, event summarization, and multimodal dialogue generation | That a recalled detail is appropriate to reuse in an unrelated task |
| **LongMemEval** [4] | Information extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention | That using a remembered preference improves a user's current outcome |
| **LaMP** [5] | Personalized outputs across seven classification and generation tasks using user profiles | That an open-ended assistant handles evolving conversational scope and privacy boundaries |
| **LongLaMP** [6] | Personalized long-form text generation | That a generated response preserves a verifiable evidence trail through memory transformations |

LoCoMo includes conversations averaging about 300 turns and 9,000 tokens, across
up to 35 sessions. Its conversations are generated through a machine-human
pipeline grounded in personas and temporal event graphs, then verified and
edited by annotators [3]. That construction supports controlled evaluation; it
is not identical to naturally accumulated, open-ended assistant use.

LongMemEval makes the evaluation problem especially concrete with 500 questions
covering five memory abilities [4]. Knowledge updates and abstention matter
because a memory system must do more than retrieve a plausible old fact.

LaMP and LongLaMP bring another necessary perspective: evaluate personalized
outputs, not only answers to questions about a history [5, 6].

These are complementary lenses. I would not interpret a strong result on any
one of them as a complete answer to whether a system personalizes responsibly.
Remembering, adapting, and respecting boundaries are related capabilities, not
interchangeable metrics.

---

## 5. Provenance: what does a memory citation actually prove?

A memory often passes through several transformations:

**Source conversation -> extracted cue -> summary or profile -> retrieved
context -> generated response.**

At every arrow, something can be lost. A summary can drop the subject. An
extraction can remove a qualifier. A profile update can overwrite a fact without
preserving why. A generated answer can attach a source that supports only part
of its claim.

A citation to the latest summary is therefore not necessarily enough. We need
to know whether the underlying evidence still supports the memory in its
current form.

![Two provenance branches start from the father's step-free access requirement. One loses the subject and incorrectly assigns the need to the user; the other preserves the subject and excludes the cue from a solo-trip answer.]({{ '/images/memory/03_provenance_branches.svg' | relative_url }})

*Figure 2. A source link is not enough: the cited evidence must support the
claim's subject and scope. These transformations are deliberately constructed
examples, not LLM outputs. [Open full-size figure]({{ '/images/memory/03_provenance_branches.svg' | relative_url }}).*

The ALCE work on generating text with citations separates answer quality from
citation quality and evaluates whether generated statements have supporting
evidence [7]. That distinction is useful for memory, even though ALCE is not
itself a benchmark for private conversational memory.

I would separate three questions:

1. **Evidence support:** does the cited source support this particular claim,
   including its subject, time, and qualifiers?
2. **Lineage:** can we trace the memory through extraction, compression, and
   updates back to the authorized source evidence?
3. **Influence:** did this memory actually change the response?

The third is not answered by the first two. A model can provide a valid citation
after generating an answer it would have produced anyway. Recording that a cue
was retrieved or included in context establishes exposure, not causal influence.

Controlled runs with and without the cue can provide evidence of influence on
the output, but even those interventions do not prove a particular internal
reasoning path.

For the restaurant example, a user-facing explanation might say:

> "I included places with fish and vegetarian options based on your June
> dietary update."

That explanation should link to the relevant, accessible source span, not an
entire conversation that happens to contain it. It should not expose unrelated
private details or become available to someone who lacks access to the source.
In an ordinary response, an on-demand "why this suggestion?" explanation may be
more useful than displaying every memory citation inline.

**Good provenance makes a claim inspectable. It does not automatically make
the claim true, the reuse appropriate, or the personalization useful.**

---

## 6. Privacy is not just removing names

The ethically difficult question is not only what we can extract from previous
conversations. It is what we should carry forward, for which purpose, and with
what opportunity for the user to inspect, correct, or remove it.

Nissenbaum's contextual integrity framework is useful here: privacy depends on
appropriate information flows within a context, not merely whether information
is secret or publicly available [8].

Applied to memory, this means a detail shared for one purpose is not blanket
permission to reuse it everywhere. A health-related conversation should not
casually shape a professional introduction. A family member's circumstances
should not become the user's profile. An inferred sensitive attribute should
not become an asserted fact because it appears predictive.

Some practical implications:

- **Minimize what is retained.** More conversational data is not automatically
  better memory.
- **Distinguish disclosure from permission.** Saying something in a chat does
  not, by itself, authorize indefinite retention or cross-context use.
- **Apply access checks before retrieval and explanation.** A citation must not
  become a route around the source's access controls.
- **Make correction and deletion operational.** Test that removed information
  cannot resurface through derived summaries, embeddings, caches, or profiles.
- **Treat evaluation data as sensitive too.** Prefer synthetic or appropriately
  consented histories; restrict access and retention for traces and annotations.
  Redaction alone is not a privacy guarantee.

These are requirements to evaluate, not a claim that metadata or citations alone
provide privacy preservation. Retention and deletion also need explicit,
documented semantics, including how backups are handled and when deletion
becomes effective.

---

## 7. An evaluation design I would trust more

I would evaluate the memory pipeline in layers and then test the user-facing
outcome. Otherwise a final-answer score hides where the system went wrong.

### Start with histories where the distinctions matter

Build authorized test histories containing updates, exceptions, third-party
facts, ambiguous references, overlapping topics, and details that should not
transfer across contexts.

Include cases where there is **no useful memory to apply**. If every test rewards
recall, we train ourselves to mistake unnecessary personalization for success.

Each test should specify the current task, the source evidence, relevant time,
acceptable cues, disallowed cues, and the expected behavior: use, ignore,
clarify, or abstain. Some tasks admit several valid cue sets; annotation should
allow that rather than assume one canonical personal profile.

### Evaluate cue selection before grading the prose

| Layer | What to measure |
|---|---|
| Extraction | Supported claims with the correct subject, scope, and qualifiers; unsupported-inference rate |
| Retrieval and ranking | Precision@k and recall@k over annotated eligible cues; graded ranking quality where relevance differs |
| Temporal handling | Correct resolution of updates and exceptions at the query time; stale-memory use rate |
| Provenance | Claim-level evidence support, citation coverage, and traceability through derived memories |
| Boundary handling | Unauthorized reuse, third-party conflation, and deleted-memory resurfacing rates |
| End-to-end utility | Task success and user preference compared with an otherwise matched no-memory baseline |
| Restraint | Appropriate non-use and clarification; unnecessary memory use when no eligible cue exists |

For retrieval, define *eligible* using both task relevance and allowed reuse.
A semantically relevant but prohibited cue should not count as a successful hit.
An empty eligible set needs its own non-use measure, not a forced recall score.

For provenance, report both whether attached citations support their claims and
whether claims requiring support actually have it. One does not substitute for
the other.

### Test whether memory improves the outcome

For the same current request, compare:

- **No historical memory:** the current request and normal task context only.
- **Retrieved memory:** the system's actual memory-selection pipeline.
- **Oracle eligible memory:** an annotated, appropriate cue set.
- **Stress conditions:** stale, irrelevant, conflicting, or explicitly
  non-reusable cues, tested separately.

The oracle condition helps diagnose whether the bottleneck is selecting memory
or using it. Stress conditions test whether the system can reject bad cues.
Run these comparisons in isolated test state so one condition cannot write
memories that affect another.

Hold the model, task instructions, tool access, and generation settings fixed
where possible. Report memory-related token cost and latency separately. Use
repeated trials for stochastic systems and uncertainty estimates that account
for multiple tasks belonging to the same user or history.

Blinded human judgments can assess task quality and appropriateness. Users are
better positioned to judge whether a preference still fits them, but user
approval is not a substitute for access-control and privacy checks. Automated
judges can help scale evaluation, with human audits for subtle scope,
sensitivity, and attribution failures.

### Keep the trade-offs visible

Do not compress everything into one personalization score. Report benefit,
inappropriate reuse, stale-memory use, provenance quality, and cost separately,
with slices for longer histories, topic switches, and sensitive contexts.

A system that improves writing style but crosses privacy boundaries is not
simply "better on average." Likewise, a system that never uses memory may avoid
some risks while providing no personalization benefit.

The useful question is where the system improves outcomes **subject to the
boundaries it must respect**.

### A small experiment: what happens as we retrieve more?

To make the cue-selection problem concrete, I ran a deterministic experiment on
**12 fictional, one-turn conversations and eight follow-up requests**. The
history extends the restaurant example with a hotel preference, a museum
preference, a colleague's dietary requirement, task-local instructions, and an
explicitly non-reusable detail. One request asks why fish can breathe underwater:
it shares a word with the dietary memory, but needs no personalization.

Before running retrieval, I assigned gold labels to all 96 request-cue pairs.
There are **13 eligible pairs**, and seven requests have at least one eligible
cue. The labels distinguish eligible, superseded, wrong-subject, out-of-scope,
and prohibited cues. These are author-assigned judgments, not independent
annotator agreement.

I compared two methods at retrieval budgets of 1, 2, 4, and 8:

- **Lexical relevance only:** TF-IDF cosine similarity between each request and
  the original source conversation. Only positive-score matches are returned.
- **Hand-annotated metadata control:** the same ranking, filtered using supplied
  subject, topic, scope, update, and reuse metadata before taking the top results.
  The filter does not consult the gold label lists, but its annotations encode
  the distinctions being evaluated. It is not a learned capability.

The prohibited detail is intentionally present in the candidate pool as a
negative control for a broken retention pipeline. A real system should not have
retained it in the first place.

![Stacked bars measure selected cue-request pairs at budgets 1, 2, 4, and 8. Lexical retrieval increasingly includes superseded, wrong-subject, out-of-scope, and prohibited cues; the hand-annotated metadata control selects only eligible cues on this fixed dataset.]({{ '/images/memory/02_retrieval_budget.svg' | relative_url }})

*Figure 3. Measured retrieval results, plotted with Seaborn, not LLM performance. Bar heights count
selected cue-request pairs across eight requests; both panels use the same
scale. A budget is a maximum, not a requirement to fill every slot. The metadata
control's clean selections depend on the supplied annotations.
[Open full-size figure]({{ '/images/memory/02_retrieval_budget.svg' | relative_url }}).*

| Method | Maximum cues per request | Selected pairs | Eligible pairs selected | Eligible / selected | Recall of 13 eligible pairs |
|---|---:|---:|---:|---:|---:|
| Lexical | 1 | 8 | 7 | 87.5% | 53.8% |
| Lexical | 2 | 15 | 8 | 53.3% | 61.5% |
| Lexical | 4 | 24 | 10 | 41.7% | 76.9% |
| Lexical | 8 | 36 | 11 | 30.6% | 84.6% |
| Metadata control | 1 | 7 | 7 | 100% | 53.8% |
| Metadata control | 2 | 10 | 10 | 100% | 76.9% |
| Metadata control | 4 | 13 | 13 | 100% | 100% |
| Metadata control | 8 | 13 | 13 | 100% | 100% |

Increasing the lexical budget from 1 to 8 recovers four additional eligible
pairs, but also adds **24 additional ineligible pairs**. At the largest budget,
the 25 ineligible selections comprise three superseded, ten wrong-subject, nine
out-of-scope, and three prohibited pairs. These are selection events, not 25
observed bad answers.

The no-personalization request is revealing too: lexical retrieval selects the
fish-related dietary statement even though the question is about biology. The
metadata control selects nothing. On this one negative case, abstention is more
appropriate than a superficially relevant match.

The control recovers all 13 eligible pairs by a budget of 4. That is not evidence
that responsible memory is solved: I supplied the subject, scope, permissions,
and update information by hand. Inferring and maintaining those annotations
reliably is much of the real problem. Filtering also cannot recover a cue with
zero lexical overlap, even though no eligible pair has that limitation here.

**What this demonstrates:** in this fixed example, a larger retrieval budget
improves eligible recall while admitting more inappropriate context.
**What it does not demonstrate:** that an LLM would use every retrieved cue,
that users would prefer one generated answer, or that a production system
preserves privacy. There are no LLM calls, user outcomes, causal-influence
measurements, or population-level statistical claims in this experiment.

The [dataset and reproduction instructions](https://github.com/reshmighosh/reshmighosh.github.io/tree/master/experiments/memory-provenance)
include the fixed annotations, Python runner, focused tests,
per-selection CSV, and aggregate JSON with an input-data hash. The code has no
external dependencies for retrieval and evaluation; regenerating Figure 3
requires the pinned Seaborn and Matplotlib plotting dependencies.

---

## Closing thought

The promise of memory is continuity: not having to explain yourself from scratch
every time. But continuity is not the same as accumulating a larger profile.

A trustworthy assistant needs to remember selectively, update carefully, and
leave room for the user to change. It needs to distinguish "you said this once"
from "this still describes you," and "I can retrieve this" from "I should use it
here."

That is why memory evaluation and provenance belong together. Evaluation asks
whether a cue helped. Provenance lets us inspect what the cue meant, where it
came from, and whether its transformation was justified. Privacy constrains
whether that information should participate at all.

**The goal is not an assistant that remembers the most. It is an assistant that
uses the right memory, for the right reason, within the right boundary, and can
be corrected when it gets that wrong.**

---

## References

The evaluation framework above is a proposed synthesis, not an established
benchmark protocol. The small synthetic retrieval experiment is reported
separately and should not be read as a real-user or LLM evaluation.

1. Gediminas Adomavicius and Alexander Tuzhilin.
   [Toward the Next Generation of Recommender Systems: A Survey of the State-of-the-Art and Possible Extensions](https://doi.org/10.1109/TKDE.2005.99).
   *IEEE Transactions on Knowledge and Data Engineering*, 2005.
2. Marti A. Hearst.
   [TextTiling: Segmenting Text into Multi-paragraph Subtopic Passages](https://aclanthology.org/J97-1003/).
   *Computational Linguistics*, 1997.
3. Adyasha Maharana et al.
   [Evaluating Very Long-Term Conversational Memory of LLM Agents](https://arxiv.org/abs/2402.17753).
   2024. [LoCoMo project](https://snap-research.github.io/locomo/).
4. Di Wu et al.
   [LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory](https://arxiv.org/abs/2410.10813).
   ICLR 2025.
5. Alireza Salemi et al.
   [LaMP: When Large Language Models Meet Personalization](https://arxiv.org/abs/2304.11406).
   2024 version.
6. Ishita Kumar et al.
   [LongLaMP: A Benchmark for Personalized Long-form Text Generation](https://arxiv.org/abs/2407.11016).
   2024.
7. Tianyu Gao et al.
   [Enabling Large Language Models to Generate Text with Citations](https://arxiv.org/abs/2305.14627).
   EMNLP 2023. Introduces ALCE.
8. Helen Nissenbaum.
   [Privacy as Contextual Integrity](https://digitalcommons.law.uw.edu/wlr/vol79/iss1/10/).
   *Washington Law Review*, 2004.
