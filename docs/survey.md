# Tool survey — what the ST computer-vision literature contains, and what we build on

Source: Zhu J, Deng R, Guo J, … Huo Y. **A comprehensive survey of computer
vision methods for spatial transcriptomics.** *Briefings in Bioinformatics*
2026;27:bbag255. doi:10.1093/bib/bbag255. Vanderbilt University + NVIDIA.

Read in full (19 pages). Two extraction caveats are stated at the end because
they limit what can be cited.

---

## 1. The review's framing

The review's argument is that spatial transcriptomics has been developed mostly
by **bioinformatics**, and that in that framing "spatial information is often
reduced to locations and relationships between molecular profiles, without
fully leveraging the wealth of sub-micron morphological detail and histological
knowledge available."

Computer-vision methods are proposed as the fix, and are claimed to address
three specific limitations of ST: **high cost, limited clinical applicability,
and reliance on 2D analysis of inherently 3D tissues.**

That third point matters for us: our dataset has serial sections.

## 2. Four vision-driven tasks

| # | Task | What it produces | Representative methods |
|---|---|---|---|
| 1 | **Generative spatial omics** | gene expression inferred from histology | ST-Net, HisToGene, EGN/EGGN, ASIGN, BLEEP, mclSTExp, OmiCLIP |
| 2 | **Vision feature encoding + clustering** | spatial domains | SpaGCN, SEPAL, STAIG |
| 3 | **Super resolution** | sub-spot / single-cell expression | HiST2ST, DeepSpaCE |
| 4 | **3D computer-vision modelling** | volumetric / cross-section reconstruction | HisToSPACE, STaCker, ASIGN |

Task 1 and task 3 are the same question at different granularity. Task 2 is a
different question. **Our two tracks map onto this directly** — Track A =
tasks 1+3, Track B = task 2.

## 3. Three learning paradigms for generative spatial omics

### (A) Regression-based
Formulates prediction as multi-dimensional regression from image features to
expression:

```
y_hat = W · MLP(f(I)) + b
```

- **ST-Net** — pretrained CNN backbone + linear projection. The origin of the
  paradigm. Weakness stated by the review: independent per-spot modelling misses
  spatial dependencies, and quality is bounded by feature quality.
- **HisToGene**, **His2ST** — add spatial coordinates so spots are connected.
- **EGN**, **EGGN** — build edges from *image similarity*, pulling visually
  similar spots together in feature space.
- **ASIGN** — extends to 3D, jointly modelling spatial relations and feature
  similarity. Moves from 2D WSI→ST prediction to **partially observed 3D
  volumetric WSI-ST imputation**.

### (B) Retrieval-based alignment
CLIP-style contrastive alignment between image and expression, then retrieve.

- **BLEEP** — first multimodal framework. Symmetric InfoNCE between image and
  expression embeddings; inference = top-K retrieval with softmax weights over a
  reference database.
- **mclSTExp** — BLEEP + spatial coordinates.
- **OmiCLIP** — 2.2 M paired samples across 32 organs; the largest alignment.
- **Review's criticism**: retrieval "relies heavily on the composition of the
  reference library, so predictions can be biased toward overrepresented
  platforms, tissues, or disease [states]." This is a real limitation for
  external cohorts — including TCGA.

### (C) Generation-based
Models the joint distribution between histology and expression.

- **STEM** — conditional diffusion, DiT backbone, histology as conditioning.
  Trained on a noise-prediction objective.
- **STFlow** — **flow matching**. Learns a deterministic time-dependent vector
  field `dx/dt = v_θ(x, t, h(I))` transporting a Gaussian prior to the
  expression distribution. The review notes this "reduces the number of sampling
  steps and improves both the stability of the generated results."

## 4. Where the review says the field is weak

1. **Gene selection.** Early work predicted highly expressed genes only, which
   "may overlook important spatial information."
2. **Reference-library dependence** in retrieval methods (above).
3. **Explainability is preliminary** — HisToGene attention maps and STimage/LIME
   exist but "remain auxiliary rather than systematic explainable AI."
4. **2D by default**, against inherently 3D tissue.

## 5. The framework we choose

**Generation-based, conditional flow matching, with cross-resolution and
cross-section conditioning.**

Reasons, in order of weight:

1. **It is the paradigm the review identifies as the frontier**, and flow
   matching specifically is credited with fewer sampling steps and more stable
   outputs. A deterministic ODE is also more reproducible than stochastic
   diffusion sampling, which matters for a benchmark paper.
2. **It outputs a distribution, not a point estimate.** That is what makes
   downstream uncertainty usable, and it is the same formalism (conditional flow
   matching) used by AlphaCell for perturbation response — so the machinery is
   transferable rather than bespoke.
3. **Our data supports the 3D axis** that the review names as under-addressed:
   27 specimens, with 12 measured by *both* Xenium and Visium, and adjacent
   sections available. ASIGN/HisToSPACE/STaCker exist but none was evaluated on
   paired single-cell + whole-transcriptome data on the same specimen.
4. **The cross-resolution objective is the actual novelty**, not the generator.
   Xenium gives single-cell targets; Visium gives whole-transcriptome targets on
   the same tumour. That permits a supervision signal no single-modality paper
   can construct.

**What we do not claim**: that a new architecture is needed. The novelty is the
training protocol and the matched ground truth, as stated in the README.

## 6. Baseline ladder

Every table carries these rows, in this order:

| Row | Why |
|---|---|
| per-slide mean expression | the trivial baseline; without it no gain is interpretable |
| PCA + ridge on H&E features | the classical baseline the field keeps omitting |
| ST-Net (regression) | the paradigm's origin |
| BLEEP-style retrieval | the strongest non-generative alignment approach |
| GHIST+ PanCancer checkpoint | the released state of the art, run locally |
| ours (conditional flow matching, cross-resolution) | |

## 7. Two extraction caveats

1. **Tables 3 and 5 are embedded as images in the PDF.** Text extraction returns
   only placeholder dots, so the numeric benchmark values in Table 5 ("all
   metrics taken directly from the original papers") **cannot be cited from this
   copy**. Quoting them would require reading the table images, which was not
   done. Any table in our manuscript therefore cites primary papers, not this
   review's summary.
2. **Coverage is as of May 2026.** VINTER (bioRxiv, October 2026) postdates the
   review and is not covered; GHIST is cited but GHIST+ is not represented as a
   reviewed method. The comparison to both is therefore built from their own
   papers and, where possible, by running their code — not from this review.
