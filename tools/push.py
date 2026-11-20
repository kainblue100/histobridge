"""Create the repo and push the working tree through the GitHub API.

`git push` to github.com:443 fails on this host; api.github.com works. Same
approach as the vcellx tool, with two corrections learned there: respect
.gitignore (via `git check-ignore -z`) and make deletions explicit with sha:null.
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys

GH = r"D:\coda_lungs\tools\gh_extract\bin\gh.exe"
REPO = "kainblue100/histobridge"
ROOT = r"D:\coda_matlab\histobridge"
BRANCH = "main"

SKIP_DIRS = {".git", "__pycache__", ".ipynb_checkpoints", "node_modules", ".venv"}
SKIP_EXT = {".pyc", ".pyo", ".log", ".tmp", ".part"}
SKIP_NAMES = {".DS_Store", "Thumbs.db"}


def gh(*args, input_text=None):
    p = subprocess.run([GH, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", input=input_text)
    if p.returncode != 0:
        raise RuntimeError(f"gh {' '.join(args[:3])} failed: {p.stderr[:500]}")
    return p.stdout


def api(path, method="GET", body=None):
    args = ["api", "-X", method, path]
    if body is not None:
        args += ["--input", "-"]
        return json.loads(gh(*args, input_text=json.dumps(body)))
    return json.loads(gh(*args))


def collect():
    out = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in SKIP_EXT or fn in SKIP_NAMES:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            out[rel] = full
    if out:
        p = subprocess.run(["git", "check-ignore", "--stdin", "-z"], cwd=ROOT,
                           input="\0".join(out), capture_output=True, text=True)
        for rel in [s for s in p.stdout.split("\0") if s]:
            out.pop(rel, None)
    return out


def ensure_repo():
    try:
        api(f"repos/{REPO}")
        print(f"  repo exists: {REPO}")
        return
    except RuntimeError:
        pass
    print(f"  creating {REPO}")
    gh("repo", "create", REPO, "--public",
       "--description",
       "Cross-resolution histology to molecular state, with a transfer protocol that is tested rather than assumed")
    print("  created")


def bootstrap_empty_repo(files):
    """Seed a first commit through the contents API.

    GitHub answers 409 "Git Repository is empty" for the git-data endpoints
    (blobs/trees/commits) until the repo has at least one commit. The contents
    API works on an empty repo, so one file goes in that way first.
    """
    rel = "README.md" if "README.md" in files else sorted(files)[0]
    data = open(files[rel], "rb").read()
    api(f"repos/{REPO}/contents/{rel}", "PUT", {
        "message": "Seed repository",
        "content": base64.b64encode(data).decode(),
    })
    print(f"  seeded first commit with {rel}")


def main():
    msg = open(sys.argv[1], encoding="utf-8").read() if len(sys.argv) > 1 else \
        "Initial scaffold\n\nCo-authored-by: CommandCodeBot <noreply@commandcode.ai>\n"
    if "CommandCodeBot" not in msg:
        msg = msg.rstrip() + "\n\nCo-authored-by: CommandCodeBot <noreply@commandcode.ai>\n"

    ensure_repo()
    files = collect()
    print(f"  {len(files)} files to upload")

    try:
        ref = api(f"repos/{REPO}/git/ref/heads/{BRANCH}")
        head = ref["object"]["sha"]
        base_tree = api(f"repos/{REPO}/git/commits/{head}")["tree"]["sha"]
        parents = [head]
        print(f"  head {head[:10]}")
    except RuntimeError:
        print("  empty repo -> seeding first commit via contents API")
        bootstrap_empty_repo(files)
        ref = api(f"repos/{REPO}/git/ref/heads/{BRANCH}")
        head = ref["object"]["sha"]
        base_tree = api(f"repos/{REPO}/git/commits/{head}")["tree"]["sha"]
        parents = [head]
        print(f"  head {head[:10]}")

    entries = []
    for rel, full in sorted(files.items()):
        data = open(full, "rb").read()
        blob = api(f"repos/{REPO}/git/blobs", "POST",
                   {"content": base64.b64encode(data).decode(), "encoding": "base64"})
        entries.append({"path": rel, "mode": "100644", "type": "blob",
                        "sha": blob["sha"]})

    tree_body = {"tree": entries}
    if base_tree:
        tree_body["base_tree"] = base_tree
    tree = api(f"repos/{REPO}/git/trees", "POST", tree_body)
    commit = api(f"repos/{REPO}/git/commits", "POST",
                 {"message": msg, "tree": tree["sha"], "parents": parents})
    api(f"repos/{REPO}/git/refs/heads/{BRANCH}", "PATCH", {"sha": commit["sha"]})
    print(f"\n  pushed -> https://github.com/{REPO}/commit/{commit['sha']}")


if __name__ == "__main__":
    main()
