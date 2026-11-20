# Plan

Each stage has a **deliverable** and a **gate**. A stage that fails its gate is
reported, not skipped.

---

## Stage 0 — inventory and cohort definition

**Deliverable**
- `manifest.csv`: one row per slide, with modality, specimen, split assignment,
  paired-H&E path, expression path, label availability, QC fields
- Cohort table: how many specimens have Xenium, Visium, both, and H&E only
- Decision recorded: which slides form train / internal-val / external

**Gate**
- Every slide in the manifest opens with the reader and yields a non-empty cell
  and gene axis
- No specimen appears in two splits

**Why first**: all later claims depend on the split being specimen-level. If a
specimen leaks across splits, nothing downstream is interpretable.

---

## Stage 1 — unified reader and expression ground truth

**Deliverable**
- `slides.py` reads Xenium (cells × genes + boundaries + H&E alignment), Visium
  (spots × genes + H&E), and TCGA (H&E + bulk) through one interface
- Normalisation fixed and documented: CP10k + log1p for Visium; Xenium counts
  handled separately and the choice stated
- Gene axis: intersection reported; the intersection is what cross-platform
  training uses

**Gate**
- Marker genes (SFTPC, EPCAM, PTPRC, COL1A1, PECAM1) show the expected spatial
  pattern on at least 3 slides per modality, checked by eye and by a per-marker
  spatial autocorrelation statistic
- If a modality fails this, it is excluded from cross-resolution training and the
  exclusion is reported

---

## Stage 2 — Track A baselines (no new model yet)

**Deliverable**
- Per-slide mean-expression baseline
- PCA + ridge on H&E patch features
- **GHIST+** inference with the released PanCancer checkpoint on the same slides
- Results table with all three on the same splits

**Gate — this is the project's most important gate**
- If PCA+ridge matches or beats GHIST+, the task is not learnable from H&E on
  this data at this resolution, and the project stops here with a negative result.
- If GHIST+ is ahead, proceed.

**Why GHIST+ first, before building anything**: if the strongest released model
does not transfer to *this* cohort, a new model has no reference point and no
credible claim.

---

## Stage 3 — cross-resolution encoder (the actual contribution)

**Deliverable**
- H&E encoder (UNI2-H features or a trained CNN — decided by Stage 2 timing)
- Two heads: single-cell-style output (Xenium) and spot-style output (Visium)
- Shared latent molecular state trained so that the same specimen's two
  resolutions agree
- Ablations: no shared state, shuffled specimen pairing (the key control)

**Gate**
- Shared-state objective beats independent per-modality models on held-out
  specimens, and
- the specimen-pairing shuffle does **not** reproduce the gain

**If the shuffle reproduces the gain**, the gain came from parameter count, not
from cross-resolution structure, and the central claim is withdrawn.

---

## Stage 4 — Track B annotation

**Deliverable**
- Leiden on H&E embeddings vs pathologist / cluster labels
- VINTER: run if obtainable; otherwise literature value with a protocol note
- Shuffled-coordinate control

**Gate**
- Annotation quality is reported separately from expression quality, always
- No claim that Track A improvements imply Track B improvements

---

## Stage 5 — external validation on TCGA

**Deliverable**
- TCGA H&E downloaded according to the published protocol, manifest checksummed
- Bulk expression matched from GDC
- One-shot evaluation: predicted vs bulk, per cancer type

**Gate**
- TCGA is touched **once**. If it was used during development, the external claim
  is withdrawn and stated as such.

**Known limitation to state in the manuscript**: TCGA has bulk, not spatial,
expression. Agreement with bulk is a weaker test than spatial agreement and must
be described as such.

---

## Stage 6 — manuscript and release

**Deliverable**
- Submission-ready package: manuscript PDF, figures, supplementary tables,
  cover letter, metadata
- Repository tagged `v0.1.0`, code + configs + split files released
- A reproducibility script that regenerates every table from raw inputs

**Gate**
- Every number in the manuscript is reproducible by the released script
- Every result row includes the trivial baseline

**Not deliverable by automation**: the bioRxiv submission itself. bioRxiv has no
submission API; it requires an author account, the manuscript PDF, and a manual
web form. The package above is what the author submits.

---

## Explicit non-goals

- No clinical claim. This is not a diagnostic model.
- No claim of beating GHIST+ or VINTER on their own benchmark unless those
  benchmarks are reproduced here.
- No new architecture proposed for its own sake.
