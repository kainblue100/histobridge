"""Stage 0: scan the data roots and emit a manifest.

This does not read expression matrices. It records what exists, what is paired
with what, and enough QC metadata to decide later whether a slide is usable.
Reading 186 GB to build a manifest would be the wrong first move.

The split assignment here is SPECIMEN-level and provisional. Stage 0's gate is
that no specimen appears in two splits; that is checked explicitly at the end.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path

DEFAULT_ROOTS = {
    "lung": "/mnt/storage/bzhang/data/lung_cancer_model",
    "tcga": "/mnt/storage/bzhang/TCGA",
}

# Xenium samples carry a specimen id of the form LUAD_No14 / TSU-21.
# Visium files carry it too (Visium_FF_LUAD_No_14, Visium_FF_TSU-19_a-1).
SPECIMEN_RE = re.compile(r"(LUAD_No\d+|TSU-?\d+)", re.IGNORECASE)


def specimen_id(name: str) -> str:
    """Normalise 'LUAD_No14' / 'LUAD_No_14' / 'TSU-21' to one key."""
    m = SPECIMEN_RE.search(name)
    if not m:
        return ""
    s = m.group(1).upper().replace("_", "")
    s = re.sub(r"TSU-?(\d+)", r"TSU-\1", s)
    return s


def size_mb(p: Path) -> float:
    try:
        return round(p.stat().st_size / 1048576, 1)
    except OSError:
        return -1.0


def scan_xenium(root: Path):
    rows = []
    raw = root / "takano_kero" / "Xenium_Raw"
    if not raw.is_dir():
        return rows
    for d in sorted(raw.iterdir()):
        if not d.is_dir():
            continue
        he = root / "takano_kero" / "Xenium_HE"
        he_hits = sorted(he.glob(f"*{d.name.split('_')[-1]}*")) if he.is_dir() else []
        rows.append({
            "modality": "xenium",
            "specimen": specimen_id(d.name),
            "sample": d.name,
            "path": str(d),
            "has_matrix": (d / "cell_feature_matrix.h5").exists(),
            "has_cells": (d / "cells.parquet").exists(),
            "has_boundaries": (d / "cell_boundaries.parquet").exists(),
            "has_morphology": (d / "morphology.ome.tif").exists(),
            "has_transcripts": (d / "transcripts.csv.gz").exists(),
            "paired_he": str(he_hits[0]) if he_hits else "",
            "size_mb": round(sum(size_mb(f) for f in d.rglob("*") if f.is_file()), 1),
        })
    return rows


def scan_visium(root: Path):
    rows = []
    seurat = root / "takano_kero" / "Visium_seurat"
    if not seurat.is_dir():
        return rows
    he_dir = root / "takano_kero" / "Visium_HE"
    for f in sorted(seurat.glob("*.rds")):
        stem = f.stem                                   # Visium_FF_LUAD_No_14
        tok = stem.replace("Visium_", "").replace("VisiumHE_", "")
        he_hits = sorted(he_dir.glob(f"*{tok}*.tif")) if he_dir.is_dir() else []
        rows.append({
            "modality": "visium",
            "specimen": specimen_id(stem),
            "sample": stem,
            "path": str(f),
            "has_matrix": True,                          # inside the Seurat object
            "has_cells": True,
            "has_boundaries": False,
            "has_morphology": bool(he_hits),
            "has_transcripts": False,
            "paired_he": str(he_hits[0]) if he_hits else "",
            "size_mb": size_mb(f),
        })
    return rows


def scan_tcga(root: Path):
    rows = []
    if not root.is_dir():
        return rows
    for f in sorted(root.rglob("*.svs")) + sorted(root.rglob("*.tif")):
        rows.append({
            "modality": "tcga_he",
            "specimen": f.stem.split(".")[0][:16],
            "sample": f.stem,
            "path": str(f),
            "has_matrix": False,
            "has_cells": False,
            "has_boundaries": False,
            "has_morphology": True,
            "has_transcripts": False,
            "paired_he": str(f),
            "size_mb": size_mb(f),
        })
    return rows


def assign_splits(rows, seed=0):
    """Provisional SPECIMEN-level split. 70/15/15 by specimen, deterministic.

    Splitting by cell or by spot would leak the same tumour into train and test,
    which is the single most common way histology-to-expression numbers become
    unreproducible.
    """
    import random
    rng = random.Random(seed)
    specs = sorted({r["specimen"] for r in rows if r["specimen"]})
    rng.shuffle(specs)
    n = len(specs)
    n_val = max(1, int(round(n * 0.15)))
    n_test = max(1, int(round(n * 0.15)))
    val = set(specs[:n_val])
    test = set(specs[n_val:n_val + n_test])
    for r in rows:
        if r["modality"] == "tcga_he":
            r["split"] = "external"
        elif r["specimen"] in test:
            r["split"] = "test"
        elif r["specimen"] in val:
            r["split"] = "val"
        else:
            r["split"] = "train"
    return specs, val, test


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "manifest.csv"))
    ap.add_argument("--lung", default=DEFAULT_ROOTS["lung"])
    ap.add_argument("--tcga", default=DEFAULT_ROOTS["tcga"])
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    root = Path(a.lung)
    rows = []
    if root.is_dir():
        rows += scan_xenium(root)
        rows += scan_visium(root)
    else:
        print(f"[warn] lung root missing: {root}")
    rows += scan_tcga(Path(a.tcga))

    if not rows:
        raise SystemExit("no slides found under any root")

    specs, val, test = assign_splits(rows, a.seed)

    cols = ["modality", "specimen", "sample", "split", "size_mb", "paired_he",
            "has_matrix", "has_cells", "has_boundaries", "has_morphology",
            "has_transcripts", "path"]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # ---- report -----------------------------------------------------------
    by_mod = {}
    for r in rows:
        by_mod.setdefault(r["modality"], []).append(r)
    print(f"wrote {out}  ({len(rows)} slides)\n")
    print(f"{'modality':12s} {'n':>4s} {'with H&E':>9s} {'with expr':>10s} {'GB':>8s}")
    for m, rs in sorted(by_mod.items()):
        he = sum(1 for r in rs if r["has_morphology"])
        ex = sum(1 for r in rs if r["has_matrix"])
        gb = sum(r["size_mb"] for r in rs) / 1024
        print(f"{m:12s} {len(rs):4d} {he:9d} {ex:10d} {gb:8.1f}")

    # ---- the gate: no specimen in two splits ------------------------------
    print("\n=== gate: specimen-level split leakage ===")
    seen = {}
    leaks = []
    for r in rows:
        if not r["specimen"] or r["modality"] == "tcga_he":
            continue
        seen.setdefault(r["specimen"], set()).add(r["split"])
    for s, sp in seen.items():
        if len(sp) > 1:
            leaks.append((s, sorted(sp)))
    if leaks:
        print(f"  *** {len(leaks)} specimens span multiple splits:")
        for s, sp in leaks[:10]:
            print(f"      {s}: {sp}")
    else:
        print(f"  PASS: {len(seen)} specimens, each in exactly one split")

    # specimens measured by both modalities are the point of the project
    both = sorted({r["specimen"] for r in rows if r["modality"] == "xenium"} &
                  {r["specimen"] for r in rows if r["modality"] == "visium"})
    print(f"\n=== specimens with BOTH Xenium and Visium: {len(both)} ===")
    print(f"  {both[:15]}{' ...' if len(both) > 15 else ''}")
    if not both:
        print("  NOTE: no overlap found by name normalisation. The cross-resolution")
        print("        objective of Stage 3 depends on this overlap; it must be")
        print("        established from sample metadata before Stage 3.")

    json.dump({"slides": len(rows),
               "specimens": len(seen),
               "both_modalities": both,
               "split_leaks": leaks,
               "by_modality": {m: len(v) for m, v in by_mod.items()}},
              open(str(out).replace(".csv", "_summary.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
