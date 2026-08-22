# Session 3 run log

Generated 2026-08-18T22:44:37+00:00 (UTC).

## Wall clock per phase

| phase | wall clock |
|---|---|
| Phase 0 inventory + pre-2024 extraction (streamed, official databento reader) | ~6 min (26 s decode CPU; rest host contention from the still-running S02 grid) |
| Phase 1 freeze | ~1 min |
| Phase 2 rules 1-7 (two passes: one detector fix, both logged) | 5m06s + 5m07s wall |
| Phase 2/3 step `load` | 1787092472.7 s CPU-side |
| Phase 2/3 step `rule1_symbology` | 1787092502.3 s CPU-side |
| Phase 2/3 step `rule2_spreads` | 1787092564.1 s CPU-side |
| Phase 2/3 step `rule3_roots` | 1787092587.3 s CPU-side |
| Phase 2/3 step `rule4_sessioncut` | 1787092616.8 s CPU-side |
| Phase 2/3 step `rule6_front` | 1787092673.3 s CPU-side |
| Phase 2/3 step `rule5_earlyclose` | 1787092702.0 s CPU-side |
| Phase 2/3 step `rule7_roll` | 1787092714.4 s CPU-side |
| Phase 2/3 step `gates` | 32.1 s CPU-side |
| Phase 2/3 step `panels_noise` | 16.9 s CPU-side |
| Phase 4 panels + noise + figure | 17 s |
| Phase 5 reports | ~1 min |

Total S03 wall clock ~45 min, inside the 90-minute budget. The S02 grid continued running throughout (its own budget accounting lives in the S02 run log); S03 was executed single-threaded to avoid starving it.

## File checksums (sha256, verified against manifest)

```text
condition.json aafd33b74eccb88295d3183bc1612b341c93e6c0e1ec44e38b73b8d7bbab3699  (match)
metadata.json  718dca4b0d756d07e5e6db53a97a6b63b80aaf13dad18adf8486c5479c4a8a7b  (match)
glbx-mdp3-20100606-20260815.ohlcv-1m.dbn.zst 08cae0bfac3eaafee5a22d2ce91076273c95166113336aa34922264fdb3fdf7f  (match)
manifest.json  ebc21d96a8de8522... (manifest carries no self-hash)
```

## Package versions (pip freeze)

```text
aiohappyeyeballs==2.7.1
aiohttp==3.14.3
aiosignal==1.4.0
attrs==26.1.0
certifi==2026.7.22
charset-normalizer==3.5.1
contourpy==1.3.3
cycler==0.12.1
databento==0.83.0
databento-dbn==0.65.0
fonttools==4.63.0
frozenlist==1.8.0
idna==3.19
iniconfig==2.3.0
kiwisolver==1.5.0
matplotlib==3.11.1
multidict==6.7.1
numpy==2.5.2
packaging==26.3
pandas==3.0.5
pillow==12.3.0
pluggy==1.6.0
propcache==0.5.2
pyarrow==25.0.1
Pygments==2.21.0
pyparsing==3.3.2
pypdf==6.16.1
pytest==9.1.1
python-dateutil==2.9.0.post0
requests==2.34.2
scipy==1.18.0
six==1.17.0
urllib3==2.7.0
yarl==1.24.5
zstandard==0.25.0
```

## Notes

- Holdout: the Phase 0 stream filtered on ts_event < 2024-01-01 at decode time; only min/max timestamps of the full file were read (span check mandated by Phase 0). No 2024+ row was decoded into any dataframe or file.
- Early-close detector was corrected once (session-max NY minute -> day-portion max; first pass reported 0, second 68); both passes are in the shell log, no data-driven tuning involved.
- One weekend trade date appears in the raw session cut (reported in the ledger); it survives no exclusion rule and is present in the final panel if it passed all rules.
- Degraded-condition dates inside the sample (condition.json): flagged in the report; no exclusion rule covers them.
