# Calibration of the shipped tests

Measured on the harness scenario (`tiergen.stats.harness.office`) with 200 seed pairs per cell and 200 permutation rounds, at level 0.05. Type I is the rejection rate between two draws of the same scenario; power is the rate against the named perturbation. A permutation test's smallest p-value is about one over the number of ways the hosts can be relabelled, so with 3 hosts against 3 (20 ways) no test can reject at 0.05 and those rows show it. Regenerate with `uv run python scripts/calibrate.py`.

| test | perturbation | hosts | hours | seeds | type I (95%) | power (95%) |
|---|---|---|---|---|---|---|
| gap_wasserstein | transition +0.1 | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.00 (0.00, 0.02) |
| gap_wasserstein | dwell x1.25 | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.00 (0.00, 0.02) |
| gap_wasserstein | rate x1.25 at 10h | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.00 (0.00, 0.02) |
| gap_ks | transition +0.1 | 3 | 2 | 200 | 0.005 (0.001, 0.028) | 0.00 (0.00, 0.02) |
| gap_ks | dwell x1.25 | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.00 (0.00, 0.02) |
| gap_ks | rate x1.25 at 10h | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.00 (0.00, 0.02) |
| mix_js | transition +0.1 | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.00 (0.00, 0.02) |
| mix_js | dwell x1.25 | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.00 (0.00, 0.02) |
| mix_js | rate x1.25 at 10h | 3 | 2 | 200 | 0.000 (0.000, 0.019) | 0.00 (0.00, 0.02) |
| transition_g | transition +0.1 | 3 | 2 | 200 | 0.015 (0.005, 0.043) | 0.04 (0.02, 0.07) |
| transition_g | dwell x1.25 | 3 | 2 | 200 | 0.010 (0.003, 0.036) | 0.01 (0.00, 0.04) |
| transition_g | rate x1.25 at 10h | 3 | 2 | 200 | 0.015 (0.005, 0.043) | 0.01 (0.01, 0.04) |
| rate_error | transition +0.1 | 3 | 2 | 200 | 0.025 (0.011, 0.057) | 0.01 (0.00, 0.04) |
| rate_error | dwell x1.25 | 3 | 2 | 200 | 0.030 (0.014, 0.064) | 0.03 (0.01, 0.06) |
| rate_error | rate x1.25 at 10h | 3 | 2 | 200 | 0.015 (0.005, 0.043) | 0.04 (0.02, 0.07) |
| gap_wasserstein | transition +0.1 | 10 | 8 | 200 | 0.090 (0.058, 0.138) | 0.62 (0.55, 0.68) |
| gap_wasserstein | dwell x1.25 | 10 | 8 | 200 | 0.090 (0.058, 0.138) | 0.32 (0.25, 0.38) |
| gap_wasserstein | rate x1.25 at 10h | 10 | 8 | 200 | 0.085 (0.054, 0.132) | 0.27 (0.21, 0.34) |
| gap_ks | transition +0.1 | 10 | 8 | 200 | 0.060 (0.035, 0.102) | 0.73 (0.66, 0.79) |
| gap_ks | dwell x1.25 | 10 | 8 | 200 | 0.060 (0.035, 0.102) | 0.81 (0.74, 0.85) |
| gap_ks | rate x1.25 at 10h | 10 | 8 | 200 | 0.060 (0.035, 0.102) | 0.20 (0.15, 0.26) |
| mix_js | transition +0.1 | 10 | 8 | 200 | 0.060 (0.035, 0.102) | 0.99 (0.96, 1.00) |
| mix_js | dwell x1.25 | 10 | 8 | 200 | 0.075 (0.046, 0.120) | 0.07 (0.04, 0.11) |
| mix_js | rate x1.25 at 10h | 10 | 8 | 200 | 0.060 (0.035, 0.102) | 0.08 (0.05, 0.13) |
| transition_g | transition +0.1 | 10 | 8 | 200 | 0.060 (0.035, 0.102) | 1.00 (0.98, 1.00) |
| transition_g | dwell x1.25 | 10 | 8 | 200 | 0.045 (0.024, 0.083) | 0.06 (0.03, 0.10) |
| transition_g | rate x1.25 at 10h | 10 | 8 | 200 | 0.060 (0.035, 0.102) | 0.07 (0.04, 0.11) |
| rate_error | transition +0.1 | 10 | 8 | 200 | 0.065 (0.038, 0.108) | 0.26 (0.20, 0.32) |
| rate_error | dwell x1.25 | 10 | 8 | 200 | 0.065 (0.038, 0.108) | 0.14 (0.10, 0.19) |
| rate_error | rate x1.25 at 10h | 10 | 8 | 200 | 0.070 (0.042, 0.114) | 0.42 (0.35, 0.49) |
| gap_wasserstein | transition +0.1 | 20 | 12 | 200 | 0.085 (0.054, 0.132) | 0.94 (0.90, 0.97) |
| gap_wasserstein | dwell x1.25 | 20 | 12 | 200 | 0.080 (0.050, 0.126) | 0.60 (0.53, 0.67) |
| gap_wasserstein | rate x1.25 at 10h | 20 | 12 | 200 | 0.070 (0.042, 0.114) | 0.37 (0.31, 0.44) |
| gap_ks | transition +0.1 | 20 | 12 | 200 | 0.070 (0.042, 0.114) | 0.98 (0.96, 0.99) |
| gap_ks | dwell x1.25 | 20 | 12 | 200 | 0.080 (0.050, 0.126) | 0.99 (0.96, 1.00) |
| gap_ks | rate x1.25 at 10h | 20 | 12 | 200 | 0.070 (0.042, 0.114) | 0.35 (0.29, 0.42) |
| mix_js | transition +0.1 | 20 | 12 | 200 | 0.065 (0.038, 0.108) | 1.00 (0.98, 1.00) |
| mix_js | dwell x1.25 | 20 | 12 | 200 | 0.060 (0.035, 0.102) | 0.07 (0.04, 0.11) |
| mix_js | rate x1.25 at 10h | 20 | 12 | 200 | 0.075 (0.046, 0.120) | 0.07 (0.04, 0.11) |
| transition_g | transition +0.1 | 20 | 12 | 200 | 0.055 (0.031, 0.096) | 1.00 (0.98, 1.00) |
| transition_g | dwell x1.25 | 20 | 12 | 200 | 0.070 (0.042, 0.114) | 0.06 (0.03, 0.10) |
| transition_g | rate x1.25 at 10h | 20 | 12 | 200 | 0.065 (0.038, 0.108) | 0.06 (0.03, 0.10) |
| rate_error | transition +0.1 | 20 | 12 | 200 | 0.080 (0.050, 0.126) | 0.66 (0.59, 0.72) |
| rate_error | dwell x1.25 | 20 | 12 | 200 | 0.095 (0.062, 0.144) | 0.24 (0.19, 0.30) |
| rate_error | rate x1.25 at 10h | 20 | 12 | 200 | 0.100 (0.066, 0.149) | 0.71 (0.65, 0.77) |
