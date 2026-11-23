"""Score every cached run with the deterministic checks and apply the release gate.

Run:  python -m evals.score                 # score all runs, write reports/
      python -m evals.score --gate sim_v2   # exit 1 if that run fails the gate (CI)
"""
import argparse
import json
import sys

import pandas as pd

from evals.checks import ALL_CHECKS, COMPLIANCE_CHECKS, run_checks
from evals.config import (GATE_MAX_COMPLIANCE_FAIL, GATE_MIN_PASS_RATE, METRICS_PATH, RUNS_DIR,
                          SCORECARD_PATH, ensure_dirs)

CHECK_NAMES = [c.__name__.removeprefix("check_") for c in ALL_CHECKS]


def score_run(path) -> pd.DataFrame:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        rec = json.loads(line)
        results = run_checks(rec["brief"], rec["payload"])
        row = {"case_id": rec["case_id"], "slice": rec["slice"]}
        row.update({r.name: r.passed for r in results})
        row["all_pass"] = all(r.passed for r in results)
        row["compliance_fail"] = any(not r.passed for r in results if r.name in COMPLIANCE_CHECKS)
        row["failures"] = "; ".join(f"{r.name}: {r.detail}" for r in results if not r.passed)
        rows.append(row)
    return pd.DataFrame(rows)


def summarise(name: str, df: pd.DataFrame) -> dict:
    pass_rate = float(df["all_pass"].mean())
    compliance_fail = float(df["compliance_fail"].mean())
    return {
        "run": name,
        "briefs": int(len(df)),
        "pass_rate": round(pass_rate, 4),
        "compliance_fail_rate": round(compliance_fail, 4),
        "per_check_pass_rate": {c: round(float(df[c].mean()), 4) for c in CHECK_NAMES},
        "pass_rate_by_slice": {s: round(float(g["all_pass"].mean()), 4) for s, g in df.groupby("slice")},
        "gate_passed": pass_rate >= GATE_MIN_PASS_RATE and compliance_fail <= GATE_MAX_COMPLIANCE_FAIL,
        "example_failures": df.loc[~df["all_pass"], ["case_id", "failures"]].head(3).to_dict(orient="records"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", help="run name that must pass the release gate")
    args = parser.parse_args()
    ensure_dirs()

    summaries = []
    for path in sorted(RUNS_DIR.glob("*.jsonl")):
        summaries.append(summarise(path.stem, score_run(path)))

    METRICS_PATH.write_text(json.dumps({"gate": {"min_pass_rate": GATE_MIN_PASS_RATE,
                                                 "max_compliance_fail_rate": GATE_MAX_COMPLIANCE_FAIL},
                                        "runs": summaries}, indent=2))
    lines = ["# Scorecard", "",
             f"Gate: pass rate >= {GATE_MIN_PASS_RATE:.0%} and compliance failures <= {GATE_MAX_COMPLIANCE_FAIL:.0%}", "",
             "| Run | Pass rate | Compliance failures | Adversarial pass | Gate |", "|---|---|---|---|---|"]
    for s in summaries:
        adv = s["pass_rate_by_slice"].get("adversarial", float("nan"))
        lines.append(f"| {s['run']} | {s['pass_rate']:.1%} | {s['compliance_fail_rate']:.1%} | {adv:.0%} | "
                     f"{'PASS' if s['gate_passed'] else 'FAIL'} |")
    lines += ["", "| Run | " + " | ".join(CHECK_NAMES) + " |", "|---|" + "---|" * len(CHECK_NAMES)]
    for s in summaries:
        lines.append(f"| {s['run']} | " + " | ".join(f"{s['per_check_pass_rate'][c]:.0%}" for c in CHECK_NAMES) + " |")
    SCORECARD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))

    if args.gate:
        s = next((x for x in summaries if x["run"] == args.gate), None)
        if s is None:
            sys.exit(f"no run named {args.gate}")
        print(f"\nGate for {args.gate}: {'PASS' if s['gate_passed'] else 'FAIL'}")
        sys.exit(0 if s["gate_passed"] else 1)


if __name__ == "__main__":
    main()
