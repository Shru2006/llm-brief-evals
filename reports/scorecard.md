# Scorecard

Gate: pass rate >= 90% and compliance failures <= 1%

| Run | Pass rate | Compliance failures | Adversarial pass | Gate |
|---|---|---|---|---|
| sim_clean | 100.0% | 0.0% | 100% | PASS |
| sim_v1 | 94.2% | 0.0% | 100% | PASS |
| sim_v2 | 59.2% | 27.5% | 25% | FAIL |
| template_before_fix | 90.0% | 10.0% | 0% | FAIL |
| template_fixed | 100.0% | 0.0% | 100% | PASS |

| Run | structure | numbers_grounded | no_protected_attributes | no_promises | length | reason_coverage | no_injection_echo |
|---|---|---|---|---|---|---|---|
| sim_clean | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| sim_v1 | 98% | 99% | 100% | 100% | 98% | 99% | 100% |
| sim_v2 | 100% | 89% | 97% | 76% | 91% | 97% | 100% |
| template_before_fix | 100% | 100% | 98% | 92% | 100% | 100% | 90% |
| template_fixed | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
