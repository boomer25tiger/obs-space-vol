# Session 4 run log

Generated 2026-08-19T00:38:39+00:00 (UTC).

## Wall clock per phase

| phase | wall |
|---|---|
| Phase 0/1 setup + freeze | ~4 min |
| Phase 2 build, 3 passes (initial + R3-patch/classifier fix + dtype fix; all logged in-session) | 3m37 + 6m49 + 7m56 wall (~40 s CPU each; the S02 grid occupies the cores) |
| Phase 3 diagnostics | 299 s |
| Phase 4 reports | ~2 min |

Total ~35 min wall, inside the 60-minute budget. Bottleneck throughout: CPU contention with the still-running S02 simulation grid (6 workers), which multiplies wall time roughly 8-10x over CPU time for pandas-heavy passes.

## Parameters used

- Early-day detector: last day-portion (ny_min < 1080) front bar before 15:00 NY.
- Designated half-days: Black Friday (Nov, Fri, day 23-29), Jul 3, Dec 24.
- Overnight completeness: >= 90% of 930 expected overnight minutes (18:00-09:29 NY).
- R3 patch: weekend-dated bars -> next Monday (2 rows).
- Extremes: |r| > 10 sd(year, root), within-session 1-minute log returns on actual bars.
- H1 anchors: 08:30, 10:00, 14:00 NY, +/-5 minutes; top-1% date bucket by ceil(0.01 x dates).
- H4: Hill on top 1% of |r| (k >= 50); t-null df = max(alpha, 2.1), scale matched to sd.
- H5: stale run = consecutive zero within-session returns immediately preceding the bar.
- D-RQ: RQ = (M/3) sum r^4; TQ tripower with mu_{4/3}; truncation at c x sqrt(BV/M), c in {3, 5, 10} (set reported, none selected); panels are the S03 forward-filled grids; log-RQ ACF lags 1-10 pooled.
- R2 dates (16) as listed in the report; diagnostics computed with and without.

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
