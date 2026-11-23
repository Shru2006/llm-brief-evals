"""Run the whole offline eval end to end with one command.

Run:  python -m evals.pipeline
"""
import sys

from evals import golden_set, meta_eval, run, score

STEPS = [
    ("1/4 Build the golden set", golden_set.main),
    ("2/4 Write briefs with every offline writer", run.main),
    ("3/4 Score runs and write the scorecard", score.main),
    ("4/4 Meta-eval: what do the checks catch?", meta_eval.main),
]


def main() -> None:
    sys.argv = sys.argv[:1]
    for title, step in STEPS:
        print(f"\n=== {title} ===")
        step()


if __name__ == "__main__":
    main()
