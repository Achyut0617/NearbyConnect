# Author-profiling model (Phase 4, Stage C)

Predicts a person's **occupation** — student / teacher / researcher / industry /
other — from their posting behaviour, with probabilities and plain-English
reasons.

## Where the data comes from (and the hard rule)
The model only ever sees a `Profile` (public post text, posting hours, hashtags),
built from **one of two allowed sources**:
1. A **licensed public benchmark** dataset, or
2. A NearbyConnect user's **own** account, analysed **with their consent**
   (`POST /me/analyze`, `consent: true`).

It is **never** run on scraped strangers. See `DECISIONS.md` (2026-11-21).

## Two models, compared
- **v1 — explainable formula** (`services/profiling/estimate.py`): a naive-Bayes
  scorer with hand-set, inspectable weights. No training. Every prediction lists
  the evidence that drove it.
- **v2 — trained model** (`services/profiling/model.py`): logistic regression
  over the same features (`features.py`), learned from labelled data.

## Features (`services/profiling/features.py`)
- Share of words in each occupation's signal vocabulary
- Hashtag category counts
- Posting-time profile (late-night / morning / work-hours share)
- Post volume and vocabulary richness

## Evaluation (`scripts/train_profiling.py`)
Run: `python -m scripts.train_profiling --n 5000`

On a held-out **synthetic** test set (seed 42, ~1250 profiles), typical results:

| model | accuracy | calibration error (ECE) |
|-------|---------:|------------------------:|
| v1 explainable formula | ~0.85 | low |
| v2 logistic regression | ~0.98 | very low |

### Honest limitations
- These numbers are on **synthetic data** whose structure we control, so they
  are an **upper bound**, not real-world accuracy. The generator
  (`synthetic.py`) deliberately injects typos, cross-occupation vocabulary,
  duplicate accounts and missing fields to make the task non-trivial, but real
  social data is messier and more ambiguous.
- The honest next step is to validate on a licensed public benchmark (e.g. a PAN
  author-profiling dataset). The code is structured so a real labelled dataset
  drops straight into `OccupationModel.train()` / the evaluation script.
- Occupation is **probabilistic and often uncertain**; the UI shows it as an
  estimate with a confidence, never as a fact.
