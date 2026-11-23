"""Evaluate the evaluator: how many known faults do the checks catch, and how
often do they flag a clean brief?

For every standard golden case, one brief is written per fault type and wording
variant (obvious / subtle), plus one clean brief. Faults are labelled, so
detection is measured exactly.

Run:  python -m evals.meta_eval            # rule-based checks (offline)
      python -m evals.meta_eval --judge    # also the LLM judge (live, needs credentials)
"""
import argparse
import json
import random

import pandas as pd

from evals.checks import run_checks
from evals.config import REPORTS_DIR, SEED
from evals.golden_set import load
from evals.writers import FAULTS, simulated_brief

# Which check *should* fire for each fault (used to report the right-check rate).
EXPECTED_CHECK = {
    "approval_promise": "no_promises",
    "invented_number": "numbers_grounded",
    "protected_attribute": "no_protected_attributes",
    "dropped_reasons": "reason_coverage",
    "missing_opener": "structure",
    "invented_watch_out": "structure",
    "too_long": "length",
}


def build_labelled_set() -> list[dict]:
    r = random.Random(f"{SEED}-meta")
    rows = []
    for case in load():
        if case["slice"] != "standard":
            continue
        p = case["payload"]
        brief, _ = simulated_brief(p, "sim_clean", r)
        rows.append({"case_id": case["case_id"], "fault": "none", "variant": "clean", "payload": p, "brief": brief})
        for fault, variants in FAULTS.items():
            if fault == "invented_watch_out" and p.get("watch_out"):
                continue  # can only invent a watch-out when none was given
            for variant in variants:
                brief, _ = simulated_brief(p, "sim_clean", r, force_fault=(fault, variant))
                rows.append({"case_id": case["case_id"], "fault": fault, "variant": variant,
                             "payload": p, "brief": brief})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--judge", action="store_true", help="also run the live LLM judge")
    args = parser.parse_args()

    rows = build_labelled_set()
    out = []
    for row in rows:
        results = {c.name: c.passed for c in run_checks(row["brief"], row["payload"])}
        rec = {"fault": row["fault"], "variant": row["variant"],
               "rules_flagged": not all(results.values()),
               "right_check_fired": (row["fault"] != "none" and not results[EXPECTED_CHECK[row["fault"]]])}
        if args.judge:  # pragma: no cover - live only
            from evals.judge import judge_brief
            rec["judge_flagged"] = judge_brief(row["payload"], row["brief"])["flagged"]
        out.append(rec)
    df = pd.DataFrame(out)

    faulted = df[df.fault != "none"]
    table = (faulted.groupby(["fault", "variant"])
             .agg(briefs=("rules_flagged", "size"), rules_recall=("rules_flagged", "mean"),
                  right_check=("right_check_fired", "mean"))
             .reset_index())
    metrics = {
        "labelled_briefs": int(len(df)),
        "clean_briefs": int((df.fault == "none").sum()),
        "rules_false_positive_rate": round(float(df.loc[df.fault == "none", "rules_flagged"].mean()), 4),
        "rules_recall_obvious": round(float(faulted.loc[faulted.variant == "obvious", "rules_flagged"].mean()), 4),
        "rules_recall_subtle": round(float(faulted.loc[faulted.variant == "subtle", "rules_flagged"].mean()), 4),
        "by_fault": table.round(4).to_dict(orient="records"),
    }
    if args.judge:  # pragma: no cover - live only
        metrics["judge_false_positive_rate"] = round(float(df.loc[df.fault == "none", "judge_flagged"].mean()), 4)
        metrics["judge_recall_subtle"] = round(float(faulted.loc[faulted.variant == "subtle", "judge_flagged"].mean()), 4)

    (REPORTS_DIR / "meta_eval.json").write_text(json.dumps(metrics, indent=2))
    print(table.to_string(index=False))
    print({k: v for k, v in metrics.items() if k != "by_fault"})


if __name__ == "__main__":
    main()
