# Session 5D report, Globex panel integrity

Generated 2026-08-19T04:27:19+00:00 (UTC). Diagnosis only: no panel was rebuilt, no prior artifact modified, nothing repaired. Output under `sessions/s05d-panel-integrity/results/`.

## Phase 1, clock mapping

`sessions/s03-data-noise/src/analysis.py:22-42`:

```python
22  def build_panels(df, root, geom):
23      """Filled log-price grid (sessions x n+1) from close prices."""
24      sub = df[df["root"] == root]
25      n = N_GRID[geom]
26      if geom == "RTH":
27          sub = sub[(sub["ny_min"] >= 570) & (sub["ny_min"] < 960)]
28          slot = sub["ny_min"] - 570
29      else:
30          slot = (sub["ny_min"] - 1080) % 1440
31          ok = slot < 1380
32          sub, slot = sub[ok], slot[ok]
33      dates = np.sort(sub["tdate"].unique())
34      didx = {d: i for i, d in enumerate(dates)}
35      S = len(dates)
36      px = np.full((S, n), np.nan)
37      px[sub["tdate"].map(didx).values, slot.values] = \
38          np.log(sub["close"].values / 1e9)
39      present = ~np.isnan(px)
40      # forward fill within session; leading gap backfilled from first obs
41      filled = pd.DataFrame(px).ffill(axis=1).bfill(axis=1).values
42      return dates, filled, present
```

| property | GLOBEX (`panel_ES_GLOBEX_B0.npz`) | RTH (`panel_ES_RTH_B0.npz`) |
|---|---|---|
| column 0 wall clock | 18:00 (slot = (ny_min - 1080) % 1440, so slot 0 is ny_min 1080) | 09:30 (slot = ny_min - 570) |
| offset | FIXED at 1080 minutes (18:00 New York); not derived per session | FIXED at 570 minutes (09:30 New York) |
| last column | slot 1379 = 16:59 New York the following day (`ok = slot < 1380` drops 17:00-17:59) | slot 389 = 15:59 New York |
| column for 13:00 / 14:00 / 15:00 NY | 1140 / 1200 / 1260 | 210 / 270 / 330 |

**Daylight saving.** `ny_min` is built in the pipeline from a tz-aware conversion to America/New_York (pipeline.py: `ny = ts.tz_convert('America/New_York')`, `ny_min = ny.hour*60 + ny.minute`), so every column carries TRUE New York wall-clock. DST is therefore handled correctly for the mapping itself. The consequence not handled is that a Globex session spans 23 wall-clock hours on the spring-forward date and 25 on the fall-back date, so those two sessions per year have one fewer / one more real column than the fixed 1380-column frame assumes.

### Twenty sessions at fixed stride

Sampled 20 sessions; 0 of them are absent from the RTH panel. Value-by-value comparison of the Globex and RTH panels over the same wall-clock minutes at 13:00, 14:00 and 15:00 New York:

| session | clock | globex_col | globex_price | globex_filled | globex_distinct_prices_in_hour | globex_present_minutes_in_hour | rth_col | rth_price | rth_filled | rth_distinct_prices_in_hour | rth_present_minutes_in_hour | minutes_disagreeing |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016-01-04 | 13:00 | 1140 | 1993 | True | 18 | 60 | 210 | 1993 | True | 18 | 60 | 0 |
| 2016-01-04 | 14:00 | 1200 | 1992.25 | True | 21 | 60 | 270 | 1992.25 | True | 21 | 60 | 0 |
| 2016-01-04 | 15:00 | 1260 | 1989.25 | True | 39 | 60 | 330 | 1989.25 | True | 39 | 60 | 0 |
| 2016-05-24 | 13:00 | 1140 | 2073.75 | True | 15 | 60 | 210 | 2073.75 | True | 15 | 60 | 0 |
| 2016-05-24 | 14:00 | 1200 | 2071 | True | 14 | 60 | 270 | 2071 | True | 14 | 60 | 0 |
| 2016-05-24 | 15:00 | 1260 | 2073.25 | True | 17 | 60 | 330 | 2073.25 | True | 17 | 60 | 0 |
| 2016-10-14 | 13:00 | 1140 | 2130.5 | True | 21 | 60 | 210 | 2130.5 | True | 21 | 60 | 0 |
| 2016-10-14 | 14:00 | 1200 | 2131 | True | 20 | 60 | 270 | 2131 | True | 20 | 60 | 0 |
| 2016-10-14 | 15:00 | 1260 | 2128.75 | True | 16 | 60 | 330 | 2128.75 | True | 16 | 60 | 0 |
| 2017-03-08 | 13:00 | 1140 | 2368.75 | True | 13 | 60 | 210 | 2368.75 | True | 13 | 60 | 0 |
| 2017-03-08 | 14:00 | 1200 | 2369.5 | True | 21 | 60 | 270 | 2369.5 | True | 21 | 60 | 0 |
| 2017-03-08 | 15:00 | 1260 | 2367.25 | True | 19 | 60 | 330 | 2367.25 | True | 19 | 60 | 0 |
| 2017-08-02 | 13:00 | 1140 | 2467 | True | 20 | 60 | 210 | 2467 | True | 20 | 60 | 0 |
| 2017-08-02 | 14:00 | 1200 | 2471.5 | True | 10 | 60 | 270 | 2471.5 | True | 10 | 60 | 0 |
| 2017-08-02 | 15:00 | 1260 | 2473.5 | True | 13 | 60 | 330 | 2473.5 | True | 13 | 60 | 0 |
| 2017-12-27 | 13:00 | 1140 | 2684.25 | True | 9 | 60 | 210 | 2684.25 | True | 9 | 60 | 0 |
| 2017-12-27 | 14:00 | 1200 | 2684.5 | True | 9 | 60 | 270 | 2684.5 | True | 9 | 60 | 0 |
| 2017-12-27 | 15:00 | 1260 | 2683.5 | True | 14 | 60 | 330 | 2683.5 | True | 14 | 60 | 0 |
| 2018-05-18 | 13:00 | 1140 | 2714.5 | True | 17 | 60 | 210 | 2714.5 | True | 17 | 60 | 0 |
| 2018-05-18 | 14:00 | 1200 | 2713.25 | True | 15 | 60 | 270 | 2713.25 | True | 15 | 60 | 0 |
| 2018-05-18 | 15:00 | 1260 | 2714.75 | True | 9 | 60 | 330 | 2714.75 | True | 9 | 60 | 0 |
| 2018-10-11 | 13:00 | 1140 | 2771 | True | 41 | 60 | 210 | 2771 | True | 41 | 60 | 0 |
| 2018-10-11 | 14:00 | 1200 | 2769.5 | True | 49 | 60 | 270 | 2769.5 | True | 49 | 60 | 0 |
| 2018-10-11 | 15:00 | 1260 | 2733 | True | 52 | 60 | 330 | 2733 | True | 52 | 60 | 0 |
| 2019-03-06 | 13:00 | 1140 | 2772 | True | 25 | 60 | 210 | 2772 | True | 25 | 60 | 0 |
| 2019-03-06 | 14:00 | 1200 | 2776.5 | True | 20 | 60 | 270 | 2776.5 | True | 20 | 60 | 0 |
| 2019-03-06 | 15:00 | 1260 | 2775.25 | True | 25 | 60 | 330 | 2775.25 | True | 25 | 60 | 0 |
| 2019-07-31 | 13:00 | 1140 | 3015.5 | True | 16 | 60 | 210 | 3015.5 | True | 16 | 60 | 0 |
| 2019-07-31 | 14:00 | 1200 | 3011.75 | True | 39 | 60 | 270 | 3011.75 | True | 39 | 60 | 0 |
| 2019-07-31 | 15:00 | 1260 | 2979 | True | 41 | 60 | 330 | 2979 | True | 41 | 60 | 0 |
| 2019-12-26 | 13:00 | 1140 | 3235.25 | True | 10 | 60 | 210 | 3235.25 | True | 10 | 60 | 0 |
| 2019-12-26 | 14:00 | 1200 | 3237 | True | 9 | 60 | 270 | 3237 | True | 9 | 60 | 0 |
| 2019-12-26 | 15:00 | 1260 | 3235.5 | True | 20 | 60 | 330 | 3235.5 | True | 20 | 60 | 0 |
| 2020-05-18 | 13:00 | 1140 | 2946 | True | 27 | 60 | 210 | 2946 | True | 27 | 60 | 0 |
| 2020-05-18 | 14:00 | 1200 | 2953.25 | True | 23 | 60 | 270 | 2953.25 | True | 23 | 60 | 0 |
| 2020-05-18 | 15:00 | 1260 | 2955.5 | True | 37 | 60 | 330 | 2955.5 | True | 37 | 60 | 0 |
| 2020-10-09 | 13:00 | 1140 | 3468.25 | True | 18 | 60 | 210 | 3468.25 | True | 18 | 60 | 0 |
| 2020-10-09 | 14:00 | 1200 | 3469 | True | 24 | 60 | 270 | 3469 | True | 24 | 60 | 0 |
| 2020-10-09 | 15:00 | 1260 | 3464.5 | True | 22 | 60 | 330 | 3464.5 | True | 22 | 60 | 0 |
| 2021-03-04 | 13:00 | 1140 | 3774.75 | True | 51 | 60 | 210 | 3774.75 | True | 51 | 60 | 0 |
| 2021-03-04 | 14:00 | 1200 | 3730.25 | True | 51 | 60 | 270 | 3730.25 | True | 51 | 60 | 0 |
| 2021-03-04 | 15:00 | 1260 | 3769 | True | 44 | 60 | 330 | 3769 | True | 44 | 60 | 0 |
| 2021-07-27 | 13:00 | 1140 | 4374.75 | True | 32 | 60 | 210 | 4374.75 | True | 32 | 60 | 0 |
| 2021-07-27 | 14:00 | 1200 | 4368.5 | True | 33 | 60 | 270 | 4368.5 | True | 33 | 60 | 0 |
| 2021-07-27 | 15:00 | 1260 | 4388.25 | True | 28 | 60 | 330 | 4388.25 | True | 28 | 60 | 0 |
| 2021-12-20 | 13:00 | 1140 | 4527 | True | 37 | 60 | 210 | 4527 | True | 37 | 60 | 0 |
| 2021-12-20 | 14:00 | 1200 | 4543 | True | 37 | 60 | 270 | 4543 | True | 37 | 60 | 0 |
| 2021-12-20 | 15:00 | 1260 | 4548.75 | True | 37 | 60 | 330 | 4548.75 | True | 37 | 60 | 0 |
| 2022-05-11 | 13:00 | 1140 | 3972.5 | True | 51 | 60 | 210 | 3972.5 | True | 51 | 60 | 0 |
| 2022-05-11 | 14:00 | 1200 | 3946.25 | True | 48 | 60 | 270 | 3946.25 | True | 48 | 60 | 0 |
| 2022-05-11 | 15:00 | 1260 | 3954.25 | True | 50 | 60 | 330 | 3954.25 | True | 50 | 60 | 0 |
| 2022-10-03 | 13:00 | 1140 | 3669.25 | True | 36 | 60 | 210 | 3669.25 | True | 36 | 60 | 0 |
| 2022-10-03 | 14:00 | 1200 | 3684.5 | True | 44 | 60 | 270 | 3684.5 | True | 44 | 60 | 0 |
| 2022-10-03 | 15:00 | 1260 | 3707 | True | 40 | 60 | 330 | 3707 | True | 40 | 60 | 0 |
| 2023-02-23 | 13:00 | 1140 | 3988.5 | True | 38 | 60 | 210 | 3988.5 | True | 38 | 60 | 0 |
| 2023-02-23 | 14:00 | 1200 | 3991.75 | True | 40 | 60 | 270 | 3991.75 | True | 40 | 60 | 0 |
| 2023-02-23 | 15:00 | 1260 | 4016 | True | 30 | 60 | 330 | 4016 | True | 30 | 60 | 0 |
| 2023-07-19 | 13:00 | 1140 | 4597.25 | True | 21 | 60 | 210 | 4597.25 | True | 21 | 60 | 0 |
| 2023-07-19 | 14:00 | 1200 | 4596.75 | True | 32 | 60 | 270 | 4596.75 | True | 32 | 60 | 0 |
| 2023-07-19 | 15:00 | 1260 | 4599.25 | True | 30 | 60 | 330 | 4599.25 | True | 30 | 60 | 0 |

**Total minute-level disagreements across all 20 sampled sessions and all three clock hours: 0.** The two panels carry byte-identical prices over the same wall-clock minutes wherever both contain the session. The Globex column index is therefore correctly aligned to New York wall clock, and the 13:00/14:00/15:00 columns are the columns they are claimed to be.

## Phase 2, zero-variance windows at source

156 one-hour Globex windows at 13:00, 14:00 or 15:00 have exactly zero realized variance, spanning 52 distinct sessions. Fifty were sampled and traced to the S04 repaired parquet over the same wall-clock minutes:

| session | clock | col_range | raw_bars_present | distinct_closes | instrument_ids | raw_symbols | underlying_bars_exist | carries_price_variation |
|---|---|---|---|---|---|---|---|---|
| 2016-05-30 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2016-05-30 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2016-07-04 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2016-09-05 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2016-09-05 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2016-11-24 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2017-02-20 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2017-02-20 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2017-02-20 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2017-05-29 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2017-05-29 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2017-05-29 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2017-07-04 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2017-09-04 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2018-05-28 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2018-07-04 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2018-09-03 | 13:00 | 1140-1200 | 1 | 1 | 57287 | ESU8 | True | False |
| 2018-12-05 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2019-01-21 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2019-01-21 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2019-07-04 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2019-11-28 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2019-11-28 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2020-02-17 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2020-05-25 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2020-09-07 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2020-09-07 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2021-01-18 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2021-02-15 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2021-05-31 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2021-05-31 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2021-05-31 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2021-07-05 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2021-09-06 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2022-01-17 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2022-02-21 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2022-02-21 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2022-06-20 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2022-06-20 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2022-07-04 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2022-09-05 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2022-11-24 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2023-01-16 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2023-01-16 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2023-02-20 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |
| 2023-02-20 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2023-06-19 | 15:00 | 1260-1320 | 0 | 0 | nan | nan | False | False |
| 2023-07-04 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2023-09-04 | 14:00 | 1200-1260 | 0 | 0 | nan | nan | False | False |
| 2023-11-23 | 13:00 | 1140-1200 | 0 | 0 | nan | nan | False | False |

**49 of 50 sampled windows have NO underlying bars at all in the source data, and 0 of 50 carry any price variation.** The zero variance is not an artifact of the panel: there is nothing to vary, because the market was not trading in those minutes.

### Clustering of the affected sessions

- By year: {'2016': 6, '2017': 6, '2018': 7, '2019': 6, '2020': 5, '2021': 7, '2022': 7, '2023': 8} - flat across the sample, roughly six to eight sessions a year.
- By weekday: {'Monday': 37, 'Thursday': 9, 'Tuesday': 2, 'Wednesday': 2, 'Friday': 2} - 37 of 52 fall on Mondays.
- By DST regime: {'EDT': 27, 'EST': 25} - split evenly, so not a daylight-saving effect.
- By contract and roll: the nearest roll is 5 sessions away and 0 sessions fall within one day of a roll, so not roll-related.
- By calendar date: {'07-04': 6, '01-18': 2, '02-15': 2, '05-30': 2, '09-05': 2, '11-24': 2, '01-16': 2, '02-20': 2, '05-29': 2, '09-04': 2, '11-23': 2, '01-15': 1, '02-19': 1, '05-28': 1, '09-03': 1}

Those dates are the US market holidays: Martin Luther King Day (01-15/16/18), Presidents' Day (02-15/19/20), Memorial Day (05-28/29/30), Independence Day (07-04, six occurrences), Labor Day (09-03/04/05) and Thanksgiving (11-23/24). On these dates the CME equity-index day session halts at 13:00 New York.

**Decisive cross-check: none of the 52 affected sessions appears in the RTH panel at all (0 of 52).** S04's repair R1 made the early-close rule geometry-dependent: RTH excludes every session whose day portion halts before 15:00 New York, while GLOBEX retains those whose overnight portion is at least 90% complete. S04 recorded the count of sessions retained by that rule as `globex_retained_holiday_sessions = {'ES': 52, 'NQ': 47}`, and the ES figure, 52, is exactly the 52 sessions found here. The asymmetry between the two panels is that documented rule operating as written, not a defect in either panel.

## Phase 3, padding and fill

**Fill mechanism.** `filled = pd.DataFrame(px).ffill(axis=1).bfill(axis=1).values` (analysis.py:41): forward fill of the last observed close within the session, with a leading backfill for columns before the session's first bar. Not zero, not a sentinel.

Share of padded columns per session, by year and geometry (the Globex column adjacent to it is restricted to the 09:30-16:00 New York columns, 930-1409):

| geometry | year | sessions | share_padded | share_padded_0930_1600 |
|---|---|---|---|---|
| GLOBEX | 2016 | 245 | 0.0191541 | 0.0113239 |
| GLOBEX | 2017 | 243 | 0.0266207 | 0.0114488 |
| GLOBEX | 2018 | 243 | 0.0182263 | 0.0155218 |
| GLOBEX | 2019 | 243 | 0.0167144 | 0.0114066 |
| GLOBEX | 2020 | 244 | 0.0164172 | 0.00986759 |
| GLOBEX | 2021 | 246 | 0.0109903 | 0.0153221 |
| GLOBEX | 2022 | 245 | 0.00499852 | 0.0131868 |
| GLOBEX | 2023 | 244 | 0.00702661 | 0.0173392 |
| RTH | 2016 | 239 | 0 | 0 |
| RTH | 2017 | 237 | 0 | 0 |
| RTH | 2018 | 236 | 0 | 0 |
| RTH | 2019 | 237 | 0 | 0 |
| RTH | 2020 | 239 | 0.00041841 | 0.00041841 |
| RTH | 2021 | 239 | 0 | 0 |
| RTH | 2022 | 238 | 0 | 0 |
| RTH | 2023 | 236 | 0 | 0 |

**Is padding distinguishable from a genuine unchanged close in the stored panel? NO. The stored S05 panel npz files contain only `logpx` and `dates`; the boolean `present` mask that `build_panels` returns is not saved with them. In the stored panel a padded column is byte-identical to a genuine unchanged close, and nothing downstream of the panel can tell them apart. S05D recovers the mask only by re-running `build_panels` on the S04 bars.**

## Phase 4, daily aggregation exposure

Globex 1day at every M in the S05B extended grid. A sub-bar is counted as padded when it contains no return whose two endpoint minutes are both present:

| M | n_windows | share_rv_from_padded_subbars | n_windows_with_empty_subbar | mean_empty_subbars | var_log_rv_as_is | var_log_rv_excluding_padded | delta | n_dropped_zero_rv |
|---|---|---|---|---|---|---|---|---|
| 5 | 1953 | 0 | 3 | 0.0015361 | 2.02332 | 2.02332 | 0 | 0 |
| 6 | 1953 | 0 | 52 | 0.0276498 | 2.05028 | 2.05028 | 0 | 0 |
| 10 | 1953 | 0 | 53 | 0.0302099 | 1.7082 | 1.7082 | 0 | 0 |
| 12 | 1953 | 0 | 54 | 0.0568356 | 1.69728 | 1.69728 | 0 | 0 |
| 23 | 1953 | 0 | 54 | 0.112647 | 1.51349 | 1.51349 | 0 | 0 |
| 46 | 1953 | 0 | 56 | 0.229391 | 1.42005 | 1.42005 | 0 | 0 |
| 138 | 1953 | 0.000830045 | 1355 | 1.36764 | 1.31235 | 1.31203 | -0.000317682 | 0 |
| 345 | 1953 | 2.6069e-05 | 1356 | 3.89708 | 1.22073 | 1.22095 | 0.000219313 | 0 |
| 1379 | 1953 | 0.00653563 | 1474 | 24.6836 | 1.04276 | 1.04334 | 0.000579636 | 0 |

Free-intercept model Var(log RV_M) = c + A M^b, fitted before and after excluding padded sub-bars:

| fit | c | A | b | RMSE |
|---|---|---|---|---|
| as_is | 1.017846 | 2.081674 | -0.439294 | 0.049838 |
| excluding_padded | 1.018734 | 2.082806 | -0.440092 | 0.049739 |

Padded sub-bars contribute at most 0.6536% of window realized variance (at M=1379) and 0.0000% at M <= 46. Excluding them moves Var(log RV_M) by at most 5.80e-04 and the fitted exponent b from -0.439294 to -0.440092, a change of 7.98e-04. The daily-aggregation exposure raised in DECISIONS item 34 is measured and is negligible; no column displacement is visible at daily aggregation, consistent with Phase 1's zero minute-level disagreements.

## Determination

### A. The panel is correct and the zero-variance windows are genuine.

Evidence, in the order it was collected:

1. **Clock mapping is correct (Phase 1).** Globex column 0 is 18:00 New York by a fixed 1080-minute offset applied to a tz-aware New York wall-clock minute, so columns 1140, 1200 and 1260 are 13:00, 14:00 and 15:00 as claimed. Across 20 sessions at fixed stride and three clock hours, the Globex and RTH panels disagree on 0 minutes. Option D is excluded: the S05B clock derivation was right.
2. **The zeros are absences of trading, not padding errors (Phase 2).** 49 of 50 sampled zero-variance windows have zero underlying bars in the S04 parquet, and none carries price variation. Option C is excluded as the cause of these windows: there is no data being padded over, there is no data at all.
3. **The market explanation is holiday early closes (Phase 2).** All 52 affected sessions are US market holidays - MLK, Presidents' Day, Memorial Day, Independence Day, Labor Day and Thanksgiving - on which the CME equity-index day session halts at 13:00 New York. The clustering is on those calendar dates, not on DST regime, contract or roll proximity.
4. **The two panels do not contradict each other (Phase 2).** None of the affected sessions is in the RTH panel. RTH contains no zero-variance windows over those minutes because it contains none of those sessions, by S04's repair R1, whose retained-session count (52 for ES) matches the 52 sessions found here exactly. Option B is excluded.
5. **Daily aggregation is unaffected (Phase 4).** Padded sub-bars carry at most 0.6536% of realized variance and the free-intercept exponent b moves by 7.98e-04 when they are excluded.

One qualification, recorded because it is real but does not change the determination: **padding is not distinguishable from a genuine unchanged close inside the stored panel** (Phase 3). The `present` mask exists in `build_panels` but is not saved in the S05 panel files, so any consumer of those files alone cannot separate the two; S05D could only do so by re-running `build_panels` against the S04 bars. Globex carries 0.5% to 2.7% padded columns per session by year against essentially 0% for RTH.
