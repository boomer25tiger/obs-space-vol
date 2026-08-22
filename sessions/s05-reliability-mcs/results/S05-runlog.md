# Session 5 run log

Generated 2026-08-19T02:06:17+00:00 (UTC).

## Wall clock per phase

| phase | wall |
|---|---|
| Phase 0 setup (arch/statsmodels install, S02 grid paused at 508/24500 to free cores; resumable) | ~5 min |
| Phase 1 freeze + calibration verification | ~4 min |
| T1 + Part A (2 runs: T1 tolerance redesigned from mean-of-ratios to ratio-of-means after the Jensen diagnosis; both runs logged) | ~1 min |
| Part C | 5 s |
| Parts D+E | see logs/partde.log timestamps (~25 min) |
| Part F (parallel, 6 workers) | see logs/partf.log (~20 min) |
| Reports | ~2 min |

## Pre-registered constants used

- NSR: 3e-5 primary; 1e-5, 1e-4 sensitivity. Hill nu: 3.4 primary; 3.0, 4.5. Boundary elevation via the measured empirical intraday profile (subsumes 25.9x/20.6x/7.5x, verified against s04_h2_minute_rates: 25.9/20.6/7.5 exact).
- Warm-up 500 windows daily, max(500, 22D+100) intraday; OLS refit each step daily / each session intraday; M5 refit every 63 sessions, Nelder-Mead, previous parameters on non-convergence (counts in s05_metrics.csv m5_nonconv).
- MCS: block length ceil(T^(1/3)), 10,000 resamples, seed 20260821; S-C conditions on the M2-HAR forecast (common predetermined variable).
- lambda for corrections: Part C E4 (TRQ3_TRV3) pooled cell at matching (root, geom, B, horizon), finest M.
- Part A/B boundary minutes: NY 09:30, 09:31, 15:59, 16:00, 18:01, bridged (zero return) in B1.
- Part F seeds: master root 20260820, masters [2092611599, 2383867976, 3610172792, 338961480, 1861959406], PCG64(SeedSequence([master, dataset_index])). Bootstrap seed 20260821. T1 seed 20260818.

## Notes

- The DECISIONS block dictated for this session numbers its items 13-16, which collides with the S04 block's 13-15; the text was appended verbatim as instructed and the collision is cosmetic.
- Prereg quotes S04 Hill range as 2.95-3.67; the S04 file records 2.98-3.67 (GLOBEX withR2). The 3.4 primary and 3.0/4.5 sensitivities cover both.

## Package versions (pip freeze)

```text
aiohappyeyeballs==2.7.1
aiohttp==3.14.3
aiosignal==1.4.0
arch==8.0.0
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
patsy==1.0.2
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
statsmodels==0.14.6
urllib3==2.7.0
yarl==1.24.5
zstandard==0.25.0
```
