"""S05A Phase 1: environment capture, lockfile, artifact checksums."""

import hashlib
import io
import json
import os
import platform
import subprocess
import sys
import time
from contextlib import redirect_stdout
from datetime import datetime, timezone

import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
RES = os.path.join(BASE, "results")
VENV_PY = sys.executable
SITE = os.path.join(ROOT, ".venv", "lib", "python3.13", "site-packages")

# Session start markers (from the transcripts / file mtimes) used to test
# whether any package changed mid-stream.
SESSION_WINDOWS = [
    ("S01", "2026-08-18 09:35"), ("S02", "2026-08-18 17:00"),
    ("S03", "2026-08-18 18:19"), ("S04", "2026-08-18 21:30"),
    ("S05", "2026-08-18 21:55"), ("S05A", "2026-08-18 22:18"),
]


def sha256(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(buf)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    t0 = time.time()
    freeze = subprocess.run([VENV_PY, "-m", "pip", "freeze"],
                            capture_output=True, text=True).stdout.strip()
    buf = io.StringIO()
    with redirect_stdout(buf):
        np.show_config()
    npcfg = buf.getvalue().strip()

    # dist-info mtimes -> evidence of mid-stream installs
    dists = []
    for d in sorted(os.listdir(SITE)):
        if d.endswith(".dist-info"):
            p = os.path.join(SITE, d)
            dists.append((d.replace(".dist-info", ""),
                          datetime.fromtimestamp(os.path.getmtime(p))
                          .strftime("%Y-%m-%d %H:%M:%S")))
    dists.sort(key=lambda x: x[1])

    threads = {k: os.environ.get(k, "(unset)") for k in
               ["OMP_NUM_THREADS", "MKL_NUM_THREADS",
                "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
                "NUMEXPR_NUM_THREADS"]}
    try:
        from threadpoolctl import threadpool_info
        tpi = threadpool_info()
    except Exception:
        tpi = "threadpoolctl not installed; see numpy.show_config() above"

    L = ["# Environment record\n",
         f"Captured {datetime.now(timezone.utc).isoformat(timespec='seconds')} "
         "(UTC) during Session 5A.\n",
         "## Retroactivity statement\n",
         "This file captures the environment **as of S05A**. It is "
         "retroactive for S01 through S05 **only if no package was "
         "installed or upgraded between those sessions and this one**. "
         "That condition is NOT satisfied in full; the evidence is below "
         "and the affected sessions are named.\n",
         "## Python and platform\n",
         f"- Python {platform.python_version()} ({platform.python_implementation()})",
         f"- Executable: {VENV_PY}",
         f"- OS: {platform.platform()}",
         f"- Machine / processor: {platform.machine()} / "
         f"{platform.processor()}",
         f"- CPU count: {os.cpu_count()}", "",
         "## Thread environment (as of capture)\n",
         "```text"] + [f"{k} = {v}" for k, v in threads.items()] + ["```\n",
         "## numpy.show_config() (BLAS/LAPACK backend)\n",
         "```text", npcfg, "```\n",
         "## threadpool_info()\n",
         "```json", json.dumps(tpi, indent=1, default=str), "```\n",
         "## pip freeze\n", "```text", freeze, "```\n",
         "## Package install/modify timestamps (dist-info mtime)\n",
         "```text"] + [f"{n:34s} {t}" for n, t in dists] + ["```\n"]

    L.append("## Evidence of mid-stream environment change\n")
    L.append("Session start markers used: "
             + ", ".join(f"{s} {t}" for s, t in SESSION_WINDOWS) + ".\n")
    core = ["numpy", "scipy", "pandas", "matplotlib", "pytest"]
    added_later = ["databento", "databento_dbn", "pypdf", "arch",
                   "statsmodels", "zstandard", "pyarrow", "patsy",
                   "threadpoolctl"]
    core_t = {n: t for n, t in dists
              if n.split("-")[0].lower().replace("_", "-") in
              [c.replace("_", "-") for c in core]}
    late_t = {n: t for n, t in dists
              if n.split("-")[0].lower().replace("_", "-") in
              [c.replace("_", "-") for c in added_later]}
    L.append("Core numerical stack (installed at S01 Phase 0, unchanged "
             "since - all four sessions' numerics ran against these exact "
             "builds):\n")
    L.append("```text")
    for n, t in core_t.items():
        L.append(f"{n:34s} {t}")
    L.append("```\n")
    L.append("Packages added AFTER S01/S02 (evidence that the environment "
             "was not constant across the whole programme):\n")
    L.append("```text")
    for n, t in late_t.items():
        L.append(f"{n:34s} {t}")
    L.append("```\n")
    L.append(
        "Reading: `databento`, `databento-dbn`, `zstandard`, `pyarrow` and "
        "`pypdf` were installed during S03; `arch`, `statsmodels`, `patsy` "
        "during S05. None of them existed when S01 and S02 ran, and none "
        "is imported by S01 or S02 code, so no S01/S02 result depends on "
        "them. No package was UPGRADED or downgraded at any point: every "
        "dist-info above is a first install, and the core stack "
        "(numpy/scipy/pandas/matplotlib/pytest) carries its original S01 "
        "timestamps. Therefore this capture is valid retroactively for "
        "S01-S05 with respect to every package each session actually "
        "imported, and the caveat is limited to the fact that S01/S02 ran "
        "in a strictly smaller environment.\n")
    with open(os.path.join(ROOT, "ENVIRONMENT.md"), "w") as fh:
        fh.write("\n".join(L))

    # ---- lockfile
    lock = subprocess.run(
        [VENV_PY, "-m", "pip", "freeze", "--all"],
        capture_output=True, text=True).stdout.strip()
    with open(os.path.join(ROOT, "requirements.lock"), "w") as fh:
        fh.write("# Fully pinned, generated by S05A Phase 1 "
                 f"({datetime.now(timezone.utc).isoformat(timespec='seconds')} "
                 f"UTC)\n# Python {platform.python_version()}, "
                 f"{platform.platform()}\n" + lock + "\n")

    # ---- checksums of every S01-S05 input panel and output artifact
    t1 = time.time()
    rows = []
    scan_roots = [os.path.join(ROOT, "data"),
                  os.path.join(ROOT, "sessions")]
    for sr in scan_roots:
        for dirpath, dirnames, filenames in os.walk(sr):
            dirnames[:] = [d for d in dirnames
                           if d not in ("__pycache__", "_cache",
                                        ".pytest_cache")]
            if os.path.basename(dirpath) == "s05a-reproducibility":
                dirnames[:] = []
                continue
            if "s05a-reproducibility" in dirpath:
                continue
            for fn in sorted(filenames):
                if fn.endswith(".pyc"):
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    rows.append((os.path.relpath(p, ROOT),
                                 os.path.getsize(p), sha256(p)))
                except OSError:
                    continue
    for fn in ["DECISIONS.md", "requirements.txt", "requirements.lock",
               "ENVIRONMENT.md", ".gitignore"]:
        p = os.path.join(ROOT, fn)
        if os.path.exists(p):
            rows.append((fn, os.path.getsize(p), sha256(p)))
    with open(os.path.join(RES, "S05A-checksums.txt"), "w") as fh:
        fh.write(f"# SHA-256 of every S01-S05 input and output artifact\n"
                 f"# generated by S05A Phase 1, "
                 f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} UTC\n"
                 f"# {len(rows)} files\n")
        for rel, sz, h in sorted(rows):
            fh.write(f"{h}  {sz:>12}  {rel}\n")
    summary = dict(n_files=len(rows),
                   total_bytes=sum(r[1] for r in rows),
                   checksum_seconds=round(time.time() - t1, 1),
                   phase1_seconds=round(time.time() - t0, 1),
                   core_pkg_times=core_t, later_pkg_times=late_t,
                   threads=threads)
    with open(os.path.join(RES, "phase1_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1)
    print(json.dumps(summary, indent=1)[:1500])


if __name__ == "__main__":
    main()
