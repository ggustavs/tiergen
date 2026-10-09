# Calibration of the shipped tests

Measured on the harness scenario (`tiergen.stats.harness.office`) with 200 seed pairs per cell and 100 permutation rounds, at level 0.05. Type I is the rejection rate between two draws of the same scenario; power is the rate against the named perturbation. Regenerate with `uv run python scripts/calibrate.py`.

| test | perturbation | hosts | hours | seeds | type I (95%) | power (95%) |
|---|---|---|---|---|---|---|
| gap_wasserstein | transition +0.1 | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.01 (0.00, 0.03) |
| gap_wasserstein | dwell x1.25 | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.00 (0.00, 0.02) |
| gap_wasserstein | rate x1.25 at 10h | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.01 (0.00, 0.03) |
| gap_ks | transition +0.1 | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.01 (0.00, 0.03) |
| gap_ks | dwell x1.25 | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.01 (0.00, 0.03) |
| gap_ks | rate x1.25 at 10h | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.01 (0.01, 0.04) |
| mix_js | transition +0.1 | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.01 (0.00, 0.03) |
| mix_js | dwell x1.25 | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.00 (0.00, 0.02) |
| mix_js | rate x1.25 at 10h | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.00 (0.00, 0.02) |
| transition_g | transition +0.1 | 3 | 2 | 200 | 0.025 (0.011, 0.057) | 0.07 (0.04, 0.11) |
| transition_g | dwell x1.25 | 3 | 2 | 200 | 0.025 (0.011, 0.057) | 0.01 (0.01, 0.04) |
| transition_g | rate x1.25 at 10h | 3 | 2 | 200 | 0.005 (0.001, 0.028) | 0.03 (0.01, 0.06) |
| rate_error | transition +0.1 | 3 | 2 | 200 | 0.030 (0.014, 0.064) | 0.01 (0.01, 0.04) |
| rate_error | dwell x1.25 | 3 | 2 | 200 | 0.030 (0.014, 0.064) | 0.01 (0.00, 0.04) |
| rate_error | rate x1.25 at 10h | 3 | 2 | 200 | 0.010 (0.003, 0.036) | 0.03 (0.01, 0.06) |
| gap_wasserstein | transition +0.1 | 10 | 8 | 200 | 0.080 (0.050, 0.126) | 0.61 (0.54, 0.67) |
| gap_wasserstein | dwell x1.25 | 10 | 8 | 200 | 0.075 (0.046, 0.120) | 0.32 (0.25, 0.38) |
| gap_wasserstein | rate x1.25 at 10h | 10 | 8 | 200 | 0.085 (0.054, 0.132) | 0.27 (0.21, 0.34) |
| gap_ks | transition +0.1 | 10 | 8 | 200 | 0.065 (0.038, 0.108) | 0.75 (0.69, 0.80) |
| gap_ks | dwell x1.25 | 10 | 8 | 200 | 0.065 (0.038, 0.108) | 0.81 (0.74, 0.85) |
| gap_ks | rate x1.25 at 10h | 10 | 8 | 200 | 0.055 (0.031, 0.096) | 0.20 (0.15, 0.26) |
| mix_js | transition +0.1 | 10 | 8 | 200 | 0.080 (0.050, 0.126) | 0.98 (0.96, 0.99) |
| mix_js | dwell x1.25 | 10 | 8 | 200 | 0.060 (0.035, 0.102) | 0.06 (0.03, 0.10) |
| mix_js | rate x1.25 at 10h | 10 | 8 | 200 | 0.090 (0.058, 0.138) | 0.09 (0.05, 0.13) |
| transition_g | transition +0.1 | 10 | 8 | 200 | 0.050 (0.027, 0.090) | 1.00 (0.98, 1.00) |
| transition_g | dwell x1.25 | 10 | 8 | 200 | 0.055 (0.031, 0.096) | 0.06 (0.03, 0.10) |
| transition_g | rate x1.25 at 10h | 10 | 8 | 200 | 0.065 (0.038, 0.108) | 0.07 (0.04, 0.11) |
| rate_error | transition +0.1 | 10 | 8 | 200 | 0.075 (0.046, 0.120) | 0.23 (0.18, 0.29) |
| rate_error | dwell x1.25 | 10 | 8 | 200 | 0.065 (0.038, 0.108) | 0.10 (0.07, 0.15) |
| rate_error | rate x1.25 at 10h | 10 | 8 | 200 | 0.060 (0.035, 0.102) | 0.43 (0.37, 0.50) |
| gap_wasserstein | transition +0.1 | 20 | 12 | 200 | 0.070 (0.042, 0.114) | 0.94 (0.90, 0.97) |
| gap_wasserstein | dwell x1.25 | 20 | 12 | 200 | 0.065 (0.038, 0.108) | 0.58 (0.52, 0.65) |
| gap_wasserstein | rate x1.25 at 10h | 20 | 12 | 200 | 0.070 (0.042, 0.114) | 0.34 (0.28, 0.41) |
| gap_ks | transition +0.1 | 20 | 12 | 200 | 0.090 (0.058, 0.138) | 0.98 (0.95, 0.99) |
| gap_ks | dwell x1.25 | 20 | 12 | 200 | 0.065 (0.038, 0.108) | 0.98 (0.96, 0.99) |
| gap_ks | rate x1.25 at 10h | 20 | 12 | 200 | 0.060 (0.035, 0.102) | 0.36 (0.30, 0.43) |
| mix_js | transition +0.1 | 20 | 12 | 200 | 0.070 (0.042, 0.114) | 1.00 (0.98, 1.00) |
| mix_js | dwell x1.25 | 20 | 12 | 200 | 0.085 (0.054, 0.132) | 0.04 (0.02, 0.08) |
| mix_js | rate x1.25 at 10h | 20 | 12 | 200 | 0.070 (0.042, 0.114) | 0.07 (0.04, 0.11) |
| transition_g | transition +0.1 | 20 | 12 | 200 | 0.065 (0.038, 0.108) | 1.00 (0.98, 1.00) |
| transition_g | dwell x1.25 | 20 | 12 | 200 | 0.055 (0.031, 0.096) | 0.06 (0.03, 0.10) |
| transition_g | rate x1.25 at 10h | 20 | 12 | 200 | 0.060 (0.035, 0.102) | 0.07 (0.05, 0.12) |
| rate_error | transition +0.1 | 20 | 12 | 200 | 0.070 (0.042, 0.114) | 0.66 (0.59, 0.72) |
| rate_error | dwell x1.25 | 20 | 12 | 200 | 0.095 (0.062, 0.144) | 0.23 (0.18, 0.30) |
| rate_error | rate x1.25 at 10h | 20 | 12 | 200 | 0.075 (0.046, 0.120) | 0.69 (0.63, 0.75) |
