# Synthetic memory selection case study

This is a small, deterministic illustration for the
[memory and provenance blog post](../../_posts/2026-10-26-memory-evaluations-and-provenance.md).
It contains **no real user data, LLM calls, model responses,
or measured user outcomes**. Python 3.9+ and its standard library are sufficient;
there are no packages to install.

## Reproduce

From the repository root:

```sh
python3 -m unittest discover -s experiments/memory-provenance -p 'test_*.py'
python3 experiments/memory-provenance/run.py
```

The runner writes [aggregate results](results/summary.json),
[all selected cue-request pairs](results/selections.csv), and three SVGs under
[images/memory](../../images/memory/). It records a SHA-256 hash of the input
dataset. Results and figures are deterministic; no random seed is needed.

## Design and labels

[case_study.json](case_study.json) fixes 12 one-turn fictional conversations,
their hand-extracted claims and metadata, and eight October follow-up requests.
Gold labels are explicitly assigned to all 96 request-cue pairs, before running
the retriever. There are 13 eligible pairs and one request with no eligible cue.
This is one deliberately constructed synthetic history, not eight independent
users or a representative sample.

The disjoint labels use this precedence: prohibited reuse, superseded statement,
wrong subject, wrong topic/task scope, eligible. Counts describe selected
cue-request pairs, not unique memories or generated-answer failures.

The prohibited cue is intentionally left in the lexical candidate pool as a
**negative control for a broken retention pipeline**. A real system should not
retain it in the first place. Its presence here does not model compliant storage.

## Methods

- **Lexical:** lowercase alphanumeric tokens, fixed stop words, raw term
  frequency, smoothed IDF `log((1+N)/(1+df))+1`, and cosine similarity between the
  current request and original conversation spans. Only already-observed sources
  are indexed. Query terms outside the source vocabulary are ignored. Only
  positive-score results are returned, with ascending cue ID breaking exact ties.
- **Metadata control:** apply the same ranking, then filter on hand-supplied
  subject, topic, task scope, replacement date, and reuse permission before
  taking up to `k` results. It does not read gold label lists, but its metadata
  encodes the distinctions the labels test. This is an annotation-assisted
  control, **not an independently learned privacy or memory capability**.

Both methods return **up to** 1, 2, 4, or 8 cues per request. There is no padding
with zero-score cues and no additional score threshold. Filtering cannot recover
an eligible cue with zero lexical overlap.

Precision is eligible selected pairs / all selected pairs. Recall is eligible
selected pairs / 13 gold eligible pairs (micro-averaged). Empty selections have
undefined precision, serialized as `null`. The no-eligible-cue request is evaluated
separately for correct non-use. Category counts partition selected pairs; they
are not calibrated measures of severity or end-user harm.

## Figures and limits

1. **Timeline:** an explanatory view of four cues from the same history.
2. **Retrieval budget:** measured stacked counts from this exact experiment,
   using a shared count axis across the two methods.
3. **Provenance branches:** deliberately constructed good/bad transformations of
   the father's statement, not observed LLM generations.

SVGs include accessible titles/descriptions and text labels in addition to
color. Their layout is fixed and typography has no external font dependency.

No confidence intervals or significance claims are appropriate for this fixed
toy example. It does not evaluate extraction accuracy, generated-answer quality,
causal influence, deletion propagation, adversarial robustness, or real-world
privacy preservation. Good results for the metadata control demonstrate the
effect of supplied annotations, not that those annotations are easy to infer.
