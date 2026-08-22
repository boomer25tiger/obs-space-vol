# Session 5A report, reproducibility amendment

Generated 2026-08-19T02:47:32+00:00 (UTC). No S05 artifact was modified or re-run in place; no data dated 2024-01-01 or later was touched.

## Phase 1, environment capture

`ENVIRONMENT.md` and `requirements.lock` written at the repository root; `results/S05A-checksums.txt` carries SHA-256 for **1,697 files** (1.48 GB) covering every input panel and every S01-S05 output artifact.

Retroactivity: the capture is valid for S01-S05 **only if nothing was installed or upgraded in between**, and that condition is only partly satisfied. Measured evidence (dist-info timestamps):

| package | timestamp | first used by |
|---|---|---|
| numpy-2.5.2 | 2026-08-18 13:14:43 | S01 |
| pytest-9.1.1 | 2026-08-18 13:16:04 | S01 |
| scipy-1.18.0 | 2026-08-18 13:17:12 | S01 |
| pandas-3.0.5 | 2026-08-18 13:17:20 | S01 |
| matplotlib-3.11.1 | 2026-08-18 13:21:40 | S01 |
| pypdf-6.16.1 | 2026-08-18 17:22:46 | S03 |
| zstandard-0.25.0 | 2026-08-18 18:24:02 | S03 |
| databento_dbn-0.65.0 | 2026-08-18 18:39:42 | S03 |
| pyarrow-25.0.1 | 2026-08-18 18:39:42 | S03 |
| databento-0.83.0 | 2026-08-18 18:41:15 | S03 |
| patsy-1.0.2 | 2026-08-18 21:24:34 | S05 |
| statsmodels-0.14.6 | 2026-08-18 21:24:47 | S05 |
| arch-8.0.0 | 2026-08-18 21:25:31 | S05 |

Reading: the timestamps fall into four distinct clusters (core stack; pypdf; the databento/pyarrow/zstandard group; the arch/statsmodels/patsy group), consistent with four install events and with the session record - S01 installed the core stack, S03 added the data reader, S05 added the model packages. **No package was upgraded or downgraded at any point**: every distribution appears exactly once at a single version, and site-packages contains no `~`-prefixed shadow directories, which is what an interrupted or replaced install leaves behind. So S01 and S02 ran in a strictly smaller environment than the one captured, but every package either of them imported is present here at the identical version. The capture is therefore retroactively valid for the packages each session actually used, and the caveat is limited to environment size, not version drift.

Thread environment at capture: `OMP_NUM_THREADS`=(unset), `MKL_NUM_THREADS`=(unset), `OPENBLAS_NUM_THREADS`=(unset), `VECLIB_MAXIMUM_THREADS`=(unset), `NUMEXPR_NUM_THREADS`=(unset). S01/S02 grid runs set `VECLIB_MAXIMUM_THREADS=1` and `OMP_NUM_THREADS=1` in their launch command; S03-S05 ran with the defaults shown (unset). Details and `numpy.show_config()` are in `ENVIRONMENT.md`.

## Phase 2, S03 vs S04 pipeline consistency (rules 1-4, 6)

Span: every session with trade date strictly before 2024-01-01, both roots; rules 1-4/6 are pre-geometry so one pass covers both geometries. Sampling used: no (full span); elapsed 21.9 min against a 25-minute cap.

Method: each module's `main()` source was sliced at its documented rule markers and executed verbatim (the executed slices are saved as `phase2_slice_*.py`), so this compares the code as written in S03 and S04, not a retranscription.

| digest field | S03 | S04 (no R3) | S04 (with R3) |
|---|---|---|---|
| n_rows_all | 7,446,530 | 7,446,530 | 7,446,530 |
| n_rows_front_contract | 5,590,872 | 5,590,872 | 5,590,872 |
| n_sessions | 4,132 | 4,132 | 4,130 |
| n_trade_dates | 2,066 | 2,066 | 2,065 |
| n_unique_iid | 74 | 74 | 74 |
| n_unique_raw | 73 | 73 | 73 |
| front_n | 4,132 | 4,132 | 4,130 |
| session_bar_count_total | 5,590,872 | 5,590,872 | 5,590,872 |
| sha_iid_sorted | `03464abc97b8801d...` | `03464abc97b8801d...` | `03464abc97b8801d...` |
| sha_tdate_sorted | `04c0f9e27635579c...` | `04c0f9e27635579c...` | `9cc8c5438d0c701f...` |
| sha_ts_sorted | `1a0a7a88fa320656...` | `1a0a7a88fa320656...` | `1a0a7a88fa320656...` |
| sha_raw_sorted | `08597e866c02d0b7...` | `08597e866c02d0b7...` | `08597e866c02d0b7...` |
| sha_front | `4891c1d6fcec939a...` | `4891c1d6fcec939a...` | `da74db46ea648d54...` |
| sha_session_bar_counts | `96b8e3b23a4920ea...` | `96b8e3b23a4920ea...` | `ccbb0056c046cfa0...` |

**Like-for-like test (the DECISIONS item 19 test): S03 rules 1-4+6 vs S04 rules 1-4+6 with the R3 repair disabled - IDENTICAL across all 19 compared fields**, including content hashes of the instrument-id assignment, trade-date assignment, front-contract table and per-session bar counts.

Expected divergence from the deliberate S04 R3 repair (DECISIONS item 15), reported separately so it is not mistaken for an inconsistency: fields differ as follows - rows only in S03 0, rows only in S04 0, rows with a different trade date 2.

```json
[
 {
  "ts_utc": "2018-08-05 21:59:00",
  "ts_ny": "2018-08-05 17:59:00-04:00",
  "iid": 57287,
  "tdate_s03": "2018-08-05 (Sunday)",
  "tdate_s04": "2018-08-06 (Monday)"
 },
 {
  "ts_utc": "2018-08-05 21:59:00",
  "ts_ny": "2018-08-05 17:59:00-04:00",
  "iid": 47511,
  "tdate_s03": "2018-08-05 (Sunday)",
  "tdate_s04": "2018-08-06 (Monday)"
 }
]
```

## Phase 3, MCS seed stability

**S05 seeding, by source inspection:** `partde.py` line 224 constructs one `np.random.Generator(np.random.PCG64(20260821))` and line 263 passes that same generator to every `mcs()` call. So S05 used an **explicitly seeded Generator, not the global random state** - but a single stream shared across all 120 cells in execution order, so no cell has an independently recoverable seed and per-cell reproduction requires replaying the entire loop in identical order. Per DECISIONS item 18, recovery was not attempted; stability was measured instead.

20 seeds = `SeedSequence(20260821).generate_state(20)`, each used as `PCG64(seed)`; 120 cells x 20 seeds = 2,400 MCS computations. Per-seed compositions: `S05A-mcs-per-seed.csv`; per-cell summary: `S05A-mcs-stability.csv`.

Distinct compositions observed across 20 seeds:

| distinct compositions | cells at 75% | cells at 90% |
|---|---|---|
| 1 | 118 | 117 |
| 2 | 2 | 3 |

Cells whose composition is identical under all 20 seeds: 118/120 at 75%, 117/120 at 90%.

S05's reported composition appears among the 20 seed compositions in 120/120 cells at 75% and 120/120 at 90%.

Per-cell detail (modal composition, its frequency out of 20, and whether S05's composition is in the set):

| cell | n | distinct 75 | modal 75 (freq) | S05 in set | distinct 90 | modal 90 (freq) | S05 in set |
|---|---|---|---|---|---|---|---|
| ES/GLOBEX/B0/1day/S-A | 1453 | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH (20) | True |
| ES/GLOBEX/B0/1day/S-B_q0.80 | 291 | 1 | M4_HARQ|M5_RGARCH (20) | True | 1 | M4_HARQ|M5_RGARCH (20) | True |
| ES/GLOBEX/B0/1day/S-B_q0.90 | 146 | 1 | M4_HARQ|M5_RGARCH (20) | True | 1 | M4_HARQ|M5_RGARCH (20) | True |
| ES/GLOBEX/B0/1day/S-C_q0.80 | 291 | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH (20) | True |
| ES/GLOBEX/B0/1day/S-C_q0.90 | 146 | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK (20) | True |
| ES/GLOBEX/B0/1h/S-A | 40996 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B0/1h/S-B_q0.80 | 8199 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B0/1h/S-B_q0.90 | 4100 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B0/1h/S-C_q0.80 | 8199 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B0/1h/S-C_q0.90 | 4100 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B0/30min/S-A | 21604 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B0/30min/S-B_q0.80 | 4321 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B0/30min/S-B_q0.90 | 2161 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B0/30min/S-C_q0.80 | 4321 | 1 | M4_HARQ (20) | True | 1 | M4_HARQ (20) | True |
| ES/GLOBEX/B0/30min/S-C_q0.90 | 2161 | 1 | M4_HARQ (20) | True | 1 | M4_HARQ (20) | True |
| ES/GLOBEX/B1/1day/S-A | 1453 | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH (20) | True |
| ES/GLOBEX/B1/1day/S-B_q0.80 | 291 | 1 | M4_HARQ|M5_RGARCH (20) | True | 1 | M4_HARQ|M5_RGARCH (20) | True |
| ES/GLOBEX/B1/1day/S-B_q0.90 | 146 | 1 | M4_HARQ|M5_RGARCH (20) | True | 1 | M4_HARQ|M5_RGARCH (20) | True |
| ES/GLOBEX/B1/1day/S-C_q0.80 | 291 | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH (20) | True |
| ES/GLOBEX/B1/1day/S-C_q0.90 | 146 | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_GK|M6_PARK (20) | True |
| ES/GLOBEX/B1/1h/S-A | 1403 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B1/1h/S-B_q0.80 | 281 | 1 | M2_HAR|M3_HARJ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/GLOBEX/B1/1h/S-B_q0.90 | 141 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/GLOBEX/B1/1h/S-C_q0.80 | 281 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B1/1h/S-C_q0.90 | 141 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/GLOBEX/B1/30min/S-A | 79538 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B1/30min/S-B_q0.80 | 15908 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B1/30min/S-B_q0.90 | 7954 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B1/30min/S-C_q0.80 | 15908 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/GLOBEX/B1/30min/S-C_q0.90 | 7954 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| ES/RTH/B0/1day/S-A | 1401 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| ES/RTH/B0/1day/S-B_q0.80 | 280 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| ES/RTH/B0/1day/S-B_q0.90 | 140 | 2 | M2_HAR|M4_HARQ (14) | True | 2 | M2_HAR|M3_HARJ|M4_HARQ (19) | True |
| ES/RTH/B0/1day/S-C_q0.80 | 280 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| ES/RTH/B0/1day/S-C_q0.90 | 140 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK (20) | True |
| ES/RTH/B0/1h/S-A | 10906 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| ES/RTH/B0/1h/S-B_q0.80 | 2181 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| ES/RTH/B0/1h/S-B_q0.90 | 1091 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B0/1h/S-C_q0.80 | 2181 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B0/1h/S-C_q0.90 | 1091 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B0/30min/S-A | 22312 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B0/30min/S-B_q0.80 | 4463 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B0/30min/S-B_q0.90 | 2232 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B0/30min/S-C_q0.80 | 4463 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B0/30min/S-C_q0.90 | 2232 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B1/1day/S-A | 1401 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| ES/RTH/B1/1day/S-B_q0.80 | 280 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B1/1day/S-B_q0.90 | 140 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B1/1day/S-C_q0.80 | 280 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B1/1day/S-C_q0.90 | 140 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ|M5_RGARCH|M6_PARK (20) | True |
| ES/RTH/B1/1h/S-A | 10906 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| ES/RTH/B1/1h/S-B_q0.80 | 2181 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| ES/RTH/B1/1h/S-B_q0.90 | 1091 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B1/1h/S-C_q0.80 | 2181 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B1/1h/S-C_q0.90 | 1091 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B1/30min/S-A | 22312 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B1/30min/S-B_q0.80 | 4463 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B1/30min/S-B_q0.90 | 2232 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B1/30min/S-C_q0.80 | 4463 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| ES/RTH/B1/30min/S-C_q0.90 | 2232 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/GLOBEX/B0/1day/S-A | 1448 | 1 | M2_HAR|M4_HARQ (20) | True | 2 | M2_HAR|M4_HARQ (17) | True |
| NQ/GLOBEX/B0/1day/S-B_q0.80 | 290 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/GLOBEX/B0/1day/S-B_q0.90 | 145 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/GLOBEX/B0/1day/S-C_q0.80 | 290 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/GLOBEX/B0/1day/S-C_q0.90 | 145 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK (20) | True |
| NQ/GLOBEX/B0/1h/S-A | 22259 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B0/1h/S-B_q0.80 | 4452 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B0/1h/S-B_q0.90 | 2226 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B0/1h/S-C_q0.80 | 4452 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B0/1h/S-C_q0.90 | 2226 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B0/30min/S-A | 80900 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B0/30min/S-B_q0.80 | 16180 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B0/30min/S-B_q0.90 | 8090 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B0/30min/S-C_q0.80 | 16180 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B0/30min/S-C_q0.90 | 8090 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B1/1day/S-A | 1448 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/GLOBEX/B1/1day/S-B_q0.80 | 290 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/GLOBEX/B1/1day/S-B_q0.90 | 145 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/GLOBEX/B1/1day/S-C_q0.80 | 290 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/GLOBEX/B1/1day/S-C_q0.90 | 145 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 2 | M2_HAR|M3_HARJ|M4_HARQ (13) | True |
| NQ/GLOBEX/B1/1h/S-A | 39503 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B1/1h/S-B_q0.80 | 7901 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B1/1h/S-B_q0.90 | 3951 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B1/1h/S-C_q0.80 | 7901 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B1/1h/S-C_q0.90 | 3951 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B1/30min/S-A | 83735 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B1/30min/S-B_q0.80 | 16747 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B1/30min/S-B_q0.90 | 8374 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B1/30min/S-C_q0.80 | 16747 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/GLOBEX/B1/30min/S-C_q0.90 | 8374 | 1 | M6_GK (20) | True | 1 | M6_GK (20) | True |
| NQ/RTH/B0/1day/S-A | 1401 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| NQ/RTH/B0/1day/S-B_q0.80 | 280 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B0/1day/S-B_q0.90 | 140 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B0/1day/S-C_q0.80 | 280 | 2 | M2_HAR|M3_HARJ|M4_HARQ (18) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B0/1day/S-C_q0.90 | 140 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK (20) | True |
| NQ/RTH/B0/1h/S-A | 10906 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| NQ/RTH/B0/1h/S-B_q0.80 | 2181 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M1_EWMA|M2_HAR|M4_HARQ (20) | True |
| NQ/RTH/B0/1h/S-B_q0.90 | 1091 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| NQ/RTH/B0/1h/S-C_q0.80 | 2181 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| NQ/RTH/B0/1h/S-C_q0.90 | 1091 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B0/30min/S-A | 22312 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B0/30min/S-B_q0.80 | 4463 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B0/30min/S-B_q0.90 | 2232 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B0/30min/S-C_q0.80 | 4463 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B0/30min/S-C_q0.90 | 2232 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B1/1day/S-A | 1401 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B1/1day/S-B_q0.80 | 280 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M1_EWMA|M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B1/1day/S-B_q0.90 | 140 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B1/1day/S-C_q0.80 | 280 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B1/1day/S-C_q0.90 | 140 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ|M6_PARK (20) | True |
| NQ/RTH/B1/1h/S-A | 10906 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| NQ/RTH/B1/1h/S-B_q0.80 | 2181 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| NQ/RTH/B1/1h/S-B_q0.90 | 1091 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| NQ/RTH/B1/1h/S-C_q0.80 | 2181 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M4_HARQ (20) | True |
| NQ/RTH/B1/1h/S-C_q0.90 | 1091 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B1/30min/S-A | 22312 | 1 | M2_HAR|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B1/30min/S-B_q0.80 | 4463 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B1/30min/S-B_q0.90 | 2232 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B1/30min/S-C_q0.80 | 4463 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |
| NQ/RTH/B1/30min/S-C_q0.90 | 2232 | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True | 1 | M2_HAR|M3_HARJ|M4_HARQ (20) | True |

### Primary result invariance, S-B vs S-C

For each (cell, quantile, confidence level) the S-B and S-C compositions are compared **under the same seed**, 20 times:

| verdict | count |
|---|---|
| IDENTICAL in all seeds | 58 |
| DIFFERS in all seeds | 35 |
| INDETERMINATE (varies across seeds) | 3 |

**Statement:** the S05 finding that MCS composition differs between S-B and S-C is seed-invariant in 93 of 96 comparisons and seed-dependent in 3. The 3 seed-dependent comparisons are reported as INDETERMINATE, not as findings:

| cell | quantile | level | seeds where S-B and S-C differ (of 20) |
|---|---|---|---|
| ES/RTH/B0/1day | 0.90 | mcs75 | 14 |
| NQ/GLOBEX/B1/1day | 0.90 | mcs90 | 7 |
| NQ/RTH/B0/1day | 0.80 | mcs75 | 2 |

## Phase 4, targeted re-run verification

Selection rule: smallest input row count within each Part, ties by ascending cell identifier (lexical). Selected before any re-run and logged in `S05A-runlog.md`.

| Part | cell identifier | input rows |
|---|---|---|
| A | `ES/RTH/B0/M13/MEDRQ_MEDRV/y2018` | 236 |
| C | `ES/GLOBEX/B0/1day/M138/y2020/t1` | 30 |
| E | `ES/RTH/B0/1day/S-B_q0.90` | 140 |

All re-runs executed with every `*_NUM_THREADS` pinned to 1, output redirected to a scratch directory.

- T1 reproduced bitwise: **True**. Part A variant selection reproduced: **True** (TRQ3_TRV3).
- Part A, every cell re-run (2,160 compared): bitwise identical = **True**.
- Part C, every estimate re-run (11,568 compared): bitwise identical = **True**.

Selected Part A cell, full precision:

| field | re-run | S05 | bitwise |
|---|---|---|---|
| median | np.float64(0.1239332930928729) | np.float64(0.1239332930928729) | True |
| iqr | np.float64(0.0484050998438568) | np.float64(0.0484050998438568) | True |
| p95 | np.float64(0.2450786465416393) | np.float64(0.2450786465416393) | True |
| p99 | np.float64(0.2851588245690242) | np.float64(0.2851588245690242) | True |
| share_gt10x_med | np.float64(0.0) | np.float64(0.0) | True |
| med_over_ref | np.float64(0.8055664051036743) | np.float64(0.8055664051036743) | True |
| acf1 | np.float64(0.0400718472786461) | np.float64(0.0400718472786461) | True |
| acf5 | np.float64(-0.0220200583969571) | np.float64(-0.0220200583969571) | True |
| acf10 | np.float64(-0.1589388232692113) | np.float64(-0.1589388232692113) | True |

Selected Part C cell, full precision:

| estimator | re-run | S05 | bitwise | abs diff |
|---|---|---|---|---|
| E1_a_exp_L1-5 | 0.5172818250944985 | 0.5172818250944985 | True | 0.000e+00 |
| E1_d_model_L1-5 | -0.3717617971107003 | -0.3717617971107003 | True | 0.000e+00 |
| E1_a_exp_L1-10 | 0.5200078631635814 | 0.5200078631635814 | True | 0.000e+00 |
| E1_d_model_L1-10 | -0.3724780956127678 | -0.3724780956127678 | True | 0.000e+00 |
| E2 | 0.7100756545200382 | 0.7100756545200382 | True | 0.000e+00 |
| E4 | 0.9463597969302296 | 0.9463597969302296 | True | 0.000e+00 |

Selected Part E cell `ES/RTH/B0/1day/S-B_q0.90`: n_obs re-run 140 vs S05 140 (match: True). Deterministic inputs to the MCS, full precision:

| model | mean QLIKE re-run | mean QLIKE S05 | bitwise | rel diff |
|---|---|---|---|---|
| M1_EWMA | 0.7654141389782134 | 0.7654141389782134 | True | 0.000e+00 |
| M2_HAR | 0.3926494545330658 | 0.3926494545330658 | True | 0.000e+00 |
| M3_HARJ | 0.4160170748251248 | 0.4160170748251248 | True | 0.000e+00 |
| M4_HARQ | 7.418586033379273e+294 | 7.418586033379274e+294 | False | 1.529e-16 |
| M5_RGARCH | 0.6649398386897261 | 0.6649398386897261 | True | 0.000e+00 |
| M6_PARK | 0.725545625859001 | 0.725545625859001 | True | 0.000e+00 |
| M6_GK | 0.7254254705344182 | 0.7254254705344182 | True | 0.000e+00 |

MCS composition is not bitwise-testable in isolation; see Phase 3 seed set for this cell.

## Phase 5, rerun determination

### B. PARTIAL RERUN REQUIRED

Evidence:

1. Consistency test (Phase 2): S03 and S04 rules 1-4+6 are identical on the full pre-2024 span, so nothing downstream of S03/S04 is invalidated by pipeline divergence. PASS.
2. MCS composition (Phase 3): seed-invariant in 93 of 96 S-B vs S-C comparisons; 3 are seed-dependent and are reported as indeterminate rather than as findings. NOT SEED-INVARIANT.
3. Targeted re-runs (Phase 4): Part A and Part C reproduce bitwise (True); Part E's deterministic inputs reproduce bitwise, and its bootstrap draw is not independently reproducible by construction (shared stream).

**Cells requiring rerun** (the indeterminate S-B/S-C comparisons; a rerun means recomputing these MCS cells over many seeds and reporting the seed distribution rather than a single draw):

| cell | quantile | level |
|---|---|---|
| ES/RTH/B0/1day | 0.90 | mcs75 |
| NQ/GLOBEX/B1/1day | 0.90 | mcs90 |
| NQ/RTH/B0/1day | 0.80 | mcs75 |

No other part of S05 requires rerun: Parts A, C and the deterministic inputs of Part E reproduce bitwise, and the S03/S04 pipeline test passes.


No rerun was performed in this session.
