# histobridge

**Cross-resolution histology → molecular state, with a transfer protocol that is
tested rather than assumed.**

Status: **scaffold**. Nothing in this repository has produced a result yet. This
file states what the project is, what it is *not*, and what would have to be true
for it to succeed.

---

## 1. What this is

Histology-to-molecular models reconstruct tissue-wide molecular state from H&E.
Two recent systems define the state of the art and they solve **different
problems**, which matters for any comparison:

| System | Input | Output | Task |
|---|---|---|---|
| **GHIST+** (SydneyBioX) | H&E + nuclei segmentation | per-cell expression | expression imputation |
| **VINTER** (Univ. Tokyo) | H&E **+ measured expression + neighbourhood** | tissue-class probabilities | spatial annotation |

VINTER consumes measured expression as input; it does not predict expression.
GHIST+ predicts expression. A benchmark that puts them on one axis would be
comparing a microscope to a thermometer. This repository therefore runs **two
separate tracks** and never merges them into a single leaderboard.

`histobridge` is a third thing: a framework whose contribution is not a new
architecture but a **cross-resolution training and transfer protocol**, evaluated
with an explicit negative-control suite.

### The chosen framework

After reading the field survey (`docs/survey.md`), the framework is:

> **Generation-based conditional flow matching, from H&E to expression, with
> cross-resolution and cross-section conditioning.**

Justification, briefly: the survey identifies generation-based modelling as the
frontier and credits flow matching specifically with fewer sampling steps and
more stable outputs; a deterministic ODE is also more reproducible than
stochastic diffusion sampling, which matters for a benchmark. It outputs a
distribution rather than a point estimate, and it is the same formalism
(conditional flow matching) that AlphaCell uses for perturbation response, so
the machinery transfers rather than being bespoke.

The novelty is **not** the generator. It is that this dataset measures
single-cell (Xenium) and whole-transcriptome (Visium) targets **on the same
specimens**, which permits a supervision signal no single-modality paper can
construct.

## 2. The data we actually have

Both modalities are present on overlapping lung adenocarcinoma specimens, which
is the property that makes the protocol possible:

```
/mnt/storage/bzhang/data/lung_cancer_model       186 GB
  takano_kero/
    Xenium_Raw/     17 samples  (cell_feature_matrix.h5, cells.parquet,
                                 cell_boundaries.parquet, morphology.ome.tif,
                                 transcripts.csv.gz)
    Xenium_HE/      aligned H&E for the Xenium sections
    Visium_seurat/  Visium FF and FFPE samples as Seurat objects
    Visium_HE/      matched H&E for the Visium sections
  xenium_luad/
    xenium_takano/  processed
    xenium_vannan/  second cohort
```

- **Xenium**: single-cell resolution, targeted gene panel. Best supervision.
- **Visium**: spot resolution, whole transcriptome. Best gene coverage.
- **TCGA H&E** (`/mnt/storage/bzhang/TCGA`, currently empty): H&E only, with bulk
  expression from the GDC. This is the external test, not the training data.

## 3. Why this dataset supports a claim other papers cannot make

Xenium and Visium are measured on the **same tumours**. That permits a training
objective no single-modality paper can construct:

```
same specimen, two instruments
  ---> learn a latent molecular state shared across resolutions
  ---> test whether the H&E encoder transfers to a resolution it never saw
```

That is the novelty: **not a bigger encoder, but a transfer claim with a matched
ground truth.** If the shared-state objective does not beat independent models,
the project fails and says so.

## 4. What this project refuses to do

The session that produced this scaffold also produced the evidence for each
refusal, so they are not stylistic preferences:

1. **No claim of superiority over a baseline without the trivial baseline.** In a
   four-arm controlled experiment on a related task, all four deep arms lost to
   "predict no change" on MSE by 2.4–8.9×. Every result table here carries that
   row.
2. **No comparison against published numbers from another protocol.** GHIST+ and
   VINTER results are reproduced locally or reported as literature with an
   explicit protocol-difference note. They are never placed in the same column as
   ours without that note.
3. **No "more parameters helped" claim without a plateaus check.** A 400-model
   study found no clear data-scaling law for single-cell pretraining; a bigger
   model is a hypothesis, not an argument.
4. **No unlabelled aggregation of modalities.** Gene-expression accuracy and
   tissue-annotation accuracy are reported on separate tables, because they are
   different tasks.

## 5. Two tracks

### Track A — expression prediction from H&E
- Train: Xenium (single-cell) and Visium (spot), separately and jointly
- Baseline: **GHIST+** PanCancer and breast checkpoints, run locally
- Classical baseline: PCA + ridge on image features
- Trivial baseline: per-slide mean expression
- Metrics: per-gene Pearson/Spearman on held-out slides, marker-gene recovery,
  and downstream cell-type accuracy via scClassify on predicted expression

### Track B — tissue annotation
- Baseline: **VINTER** (if code is obtainable; otherwise literature value with a
  protocol note), plus spatial-domain clustering (Leiden on H&E embeddings)
- Negative control: shuffled spatial coordinates, shuffled labels
- Metrics: ARI / NMI / per-class F1 against pathologist annotation

## 6. Evaluation discipline (pre-registered)

Fixed before any result exists:

| Rule | Consequence if violated |
|---|---|
| Slide-level splits, never cell-level | Results are discarded |
| Trivial baseline reported in every table | Table is incomplete |
| Shuffled-label control for every learned component | Gain is unattributable |
| External set (TCGA) touched once, at the end | If used twice, no external claim |
| Two tracks reported separately | Never merged into one score |

**Go/No-Go:** if Track A does not beat both the trivial baseline and PCA+ridge on
held-out slides, the framework is reported as a negative result.

## 7. Repository layout

```
src/histobridge/
  inventory.py    scan the data roots, emit a manifest with QC fields
  slides.py       unified slide reader (Xenium / Visium / TCGA)
docs/
  survey.md       tool survey from Brief Bioinform 2026;27:bbag255
PLAN.md           staged milestones with deliverable and gate per stage
```

## 8. What is not possible here, stated up front

- **bioRxiv posting is not automatable.** bioRxiv has no submission API; it
  requires an author account, a linked ORCID, and a manual web form. This
  repository produces a submission-ready package (manuscript PDF, figures,
  supplementary, metadata). The submission itself must be performed by the
  author.
- **VINTER cannot be run head-to-head** unless its code and weights are released.
  Its comparison will be labelled as a literature value.
- **UNI2-H is a gated model.** Using it requires accepting its terms; the weights
  cannot be fetched by an unattended process.

## 9. Licence

MIT for this repository's code. Third-party models and data retain their own
terms (UNI2-H, GHIST+ bundle, TCGA, Xenium/Visium data).
