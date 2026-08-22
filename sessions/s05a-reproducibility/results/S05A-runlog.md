# Session 5A run log

## Phase 3 fixed execution order (written before the first cell computation)

Master seed 20260821; the 20 seeds are `SeedSequence(20260821).generate_state(20)` = [2237533746, 702494603, 4139393190, 769717545, 919028315, 611620464, 3477480266, 3198431117, 2621026741, 1169115867, 3689063838, 1498398406, 3833968697, 630741820, 2401719883, 3662131630, 303417529, 4155647398, 2620441196, 4201311651].

Every S-B / S-C cell runs before every S-A cell; within each stage, ascending cell identifier under lexical sort. 96 S-B/S-C cells then 24 S-A cells, 120 total, 20 seeds each = 2400 MCS computations.

```text
  1. ES/GLOBEX/B0/1day/S-B_q0.80
  2. ES/GLOBEX/B0/1day/S-B_q0.90
  3. ES/GLOBEX/B0/1day/S-C_q0.80
  4. ES/GLOBEX/B0/1day/S-C_q0.90
  5. ES/GLOBEX/B0/1h/S-B_q0.80
  6. ES/GLOBEX/B0/1h/S-B_q0.90
  7. ES/GLOBEX/B0/1h/S-C_q0.80
  8. ES/GLOBEX/B0/1h/S-C_q0.90
  9. ES/GLOBEX/B0/30min/S-B_q0.80
 10. ES/GLOBEX/B0/30min/S-B_q0.90
 11. ES/GLOBEX/B0/30min/S-C_q0.80
 12. ES/GLOBEX/B0/30min/S-C_q0.90
 13. ES/GLOBEX/B1/1day/S-B_q0.80
 14. ES/GLOBEX/B1/1day/S-B_q0.90
 15. ES/GLOBEX/B1/1day/S-C_q0.80
 16. ES/GLOBEX/B1/1day/S-C_q0.90
 17. ES/GLOBEX/B1/1h/S-B_q0.80
 18. ES/GLOBEX/B1/1h/S-B_q0.90
 19. ES/GLOBEX/B1/1h/S-C_q0.80
 20. ES/GLOBEX/B1/1h/S-C_q0.90
 21. ES/GLOBEX/B1/30min/S-B_q0.80
 22. ES/GLOBEX/B1/30min/S-B_q0.90
 23. ES/GLOBEX/B1/30min/S-C_q0.80
 24. ES/GLOBEX/B1/30min/S-C_q0.90
 25. ES/RTH/B0/1day/S-B_q0.80
 26. ES/RTH/B0/1day/S-B_q0.90
 27. ES/RTH/B0/1day/S-C_q0.80
 28. ES/RTH/B0/1day/S-C_q0.90
 29. ES/RTH/B0/1h/S-B_q0.80
 30. ES/RTH/B0/1h/S-B_q0.90
 31. ES/RTH/B0/1h/S-C_q0.80
 32. ES/RTH/B0/1h/S-C_q0.90
 33. ES/RTH/B0/30min/S-B_q0.80
 34. ES/RTH/B0/30min/S-B_q0.90
 35. ES/RTH/B0/30min/S-C_q0.80
 36. ES/RTH/B0/30min/S-C_q0.90
 37. ES/RTH/B1/1day/S-B_q0.80
 38. ES/RTH/B1/1day/S-B_q0.90
 39. ES/RTH/B1/1day/S-C_q0.80
 40. ES/RTH/B1/1day/S-C_q0.90
 41. ES/RTH/B1/1h/S-B_q0.80
 42. ES/RTH/B1/1h/S-B_q0.90
 43. ES/RTH/B1/1h/S-C_q0.80
 44. ES/RTH/B1/1h/S-C_q0.90
 45. ES/RTH/B1/30min/S-B_q0.80
 46. ES/RTH/B1/30min/S-B_q0.90
 47. ES/RTH/B1/30min/S-C_q0.80
 48. ES/RTH/B1/30min/S-C_q0.90
 49. NQ/GLOBEX/B0/1day/S-B_q0.80
 50. NQ/GLOBEX/B0/1day/S-B_q0.90
 51. NQ/GLOBEX/B0/1day/S-C_q0.80
 52. NQ/GLOBEX/B0/1day/S-C_q0.90
 53. NQ/GLOBEX/B0/1h/S-B_q0.80
 54. NQ/GLOBEX/B0/1h/S-B_q0.90
 55. NQ/GLOBEX/B0/1h/S-C_q0.80
 56. NQ/GLOBEX/B0/1h/S-C_q0.90
 57. NQ/GLOBEX/B0/30min/S-B_q0.80
 58. NQ/GLOBEX/B0/30min/S-B_q0.90
 59. NQ/GLOBEX/B0/30min/S-C_q0.80
 60. NQ/GLOBEX/B0/30min/S-C_q0.90
 61. NQ/GLOBEX/B1/1day/S-B_q0.80
 62. NQ/GLOBEX/B1/1day/S-B_q0.90
 63. NQ/GLOBEX/B1/1day/S-C_q0.80
 64. NQ/GLOBEX/B1/1day/S-C_q0.90
 65. NQ/GLOBEX/B1/1h/S-B_q0.80
 66. NQ/GLOBEX/B1/1h/S-B_q0.90
 67. NQ/GLOBEX/B1/1h/S-C_q0.80
 68. NQ/GLOBEX/B1/1h/S-C_q0.90
 69. NQ/GLOBEX/B1/30min/S-B_q0.80
 70. NQ/GLOBEX/B1/30min/S-B_q0.90
 71. NQ/GLOBEX/B1/30min/S-C_q0.80
 72. NQ/GLOBEX/B1/30min/S-C_q0.90
 73. NQ/RTH/B0/1day/S-B_q0.80
 74. NQ/RTH/B0/1day/S-B_q0.90
 75. NQ/RTH/B0/1day/S-C_q0.80
 76. NQ/RTH/B0/1day/S-C_q0.90
 77. NQ/RTH/B0/1h/S-B_q0.80
 78. NQ/RTH/B0/1h/S-B_q0.90
 79. NQ/RTH/B0/1h/S-C_q0.80
 80. NQ/RTH/B0/1h/S-C_q0.90
 81. NQ/RTH/B0/30min/S-B_q0.80
 82. NQ/RTH/B0/30min/S-B_q0.90
 83. NQ/RTH/B0/30min/S-C_q0.80
 84. NQ/RTH/B0/30min/S-C_q0.90
 85. NQ/RTH/B1/1day/S-B_q0.80
 86. NQ/RTH/B1/1day/S-B_q0.90
 87. NQ/RTH/B1/1day/S-C_q0.80
 88. NQ/RTH/B1/1day/S-C_q0.90
 89. NQ/RTH/B1/1h/S-B_q0.80
 90. NQ/RTH/B1/1h/S-B_q0.90
 91. NQ/RTH/B1/1h/S-C_q0.80
 92. NQ/RTH/B1/1h/S-C_q0.90
 93. NQ/RTH/B1/30min/S-B_q0.80
 94. NQ/RTH/B1/30min/S-B_q0.90
 95. NQ/RTH/B1/30min/S-C_q0.80
 96. NQ/RTH/B1/30min/S-C_q0.90
 97. ES/GLOBEX/B0/1day/S-A
 98. ES/GLOBEX/B0/1h/S-A
 99. ES/GLOBEX/B0/30min/S-A
100. ES/GLOBEX/B1/1day/S-A
101. ES/GLOBEX/B1/1h/S-A
102. ES/GLOBEX/B1/30min/S-A
103. ES/RTH/B0/1day/S-A
104. ES/RTH/B0/1h/S-A
105. ES/RTH/B0/30min/S-A
106. ES/RTH/B1/1day/S-A
107. ES/RTH/B1/1h/S-A
108. ES/RTH/B1/30min/S-A
109. NQ/GLOBEX/B0/1day/S-A
110. NQ/GLOBEX/B0/1h/S-A
111. NQ/GLOBEX/B0/30min/S-A
112. NQ/GLOBEX/B1/1day/S-A
113. NQ/GLOBEX/B1/1h/S-A
114. NQ/GLOBEX/B1/30min/S-A
115. NQ/RTH/B0/1day/S-A
116. NQ/RTH/B0/1h/S-A
117. NQ/RTH/B0/30min/S-A
118. NQ/RTH/B1/1day/S-A
119. NQ/RTH/B1/1h/S-A
120. NQ/RTH/B1/30min/S-A
```

## Phase 4 selected verification cells (written before any re-run)

| Part | cell identifier | input rows |
|---|---|---|
| A | `ES/RTH/B0/M13/MEDRQ_MEDRV/y2018` | 236 |
| C | `ES/GLOBEX/B0/1day/M138/y2020/t1` | 30 |
| E | `ES/RTH/B0/1day/S-B_q0.90` | 140 |

## Wall clock per phase

| phase | wall |
|---|---|
| Phase 0 (dirs, DECISIONS, S02 grid paused at 535/24500) | ~2 min |
| Phase 1 environment + 1,697 checksums | 22 s |
| Phase 2 consistency (3 pipeline executions) | 21.9 min |
| Phase 3 loss regeneration (24 groups, 6 workers) | 12.8 min |
| Phase 3 MCS, 120 cells x 20 seeds | see phase3.log |
| Phase 4 targeted re-runs | 54 s |
| Phase 5 reports | ~2 min |

## Seeds and their derivation

- Phase 3 master seed 20260821 (S05's own MCS seed). The 20 independent seeds are `numpy.random.SeedSequence(20260821).generate_state(20)`, listed in the Phase 3 order block above; each is used as `PCG64(seed)` for one cell's MCS.
- S05's own seeding, for the record: one `PCG64(20260821)` generator shared across all 120 cells in execution order (partde.py:224, consumed at partde.py:263).
- No other randomness enters S05A: Phases 1, 2 and 4 are deterministic.

## Phase 2 executed slices

`results/phase2_slice_S03.py`, `results/phase2_slice_S04_noR3.py`, `results/phase2_slice_S04_withR3.py` are the exact code blocks executed, sliced from the S03/S04 sources at their rule markers.

## Environment record

Full record in `ENVIRONMENT.md`; lockfile `requirements.lock`; checksums `results/S05A-checksums.txt` (1,697 files, 1.48 GB).

- Python 3.13.13, macOS-14.6-arm64-arm-64bit-Mach-O
- Threads at capture: OMP_NUM_THREADS=(unset), MKL_NUM_THREADS=(unset), OPENBLAS_NUM_THREADS=(unset), VECLIB_MAXIMUM_THREADS=(unset), NUMEXPR_NUM_THREADS=(unset); Phase 4 re-runs pinned all of them to 1.

### pip freeze

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
