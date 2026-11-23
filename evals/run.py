"""Generate briefs for every golden case with each writer and cache them in runs/.

Cached runs make scoring reproducible and free: CI re-scores them without any
API key. Live Claude runs are added with --writer claude (needs credentials).

Run:  python -m evals.run                      # all offline writers
      python -m evals.run --writer claude --prompt brief_v1.md   # live
"""
import argparse
import json
import random

from evals.config import RUNS_DIR, SEED, ensure_dirs
from evals.golden_set import load
from evals.writers import PROFILES, claude_brief, simulated_brief, template_brief, template_fixed_brief

OFFLINE_WRITERS = ["template_before_fix", "template_fixed", *PROFILES]


def generate(writer: str, prompt: str = "brief_v1.md") -> list[dict]:
    r = random.Random(f"{SEED}-{writer}")
    rows = []
    for case in load():
        p = case["payload"]
        if writer == "template_before_fix":
            brief, labels = template_brief(p), []
        elif writer == "template_fixed":
            brief, labels = template_fixed_brief(p), []
        elif writer in PROFILES:
            brief, labels = simulated_brief(p, writer, r)
        elif writer == "claude":  # pragma: no cover - live only
            brief, labels = claude_brief(p, prompt), []
        else:
            raise ValueError(f"unknown writer {writer}")
        rows.append({"case_id": case["case_id"], "slice": case["slice"], "payload": p,
                     "brief": brief, "injected_faults": labels})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--writer", default="offline", help="template_before_fix, template_fixed, sim_clean, sim_v1, sim_v2, claude or offline")
    parser.add_argument("--prompt", default="brief_v1.md")
    args = parser.parse_args()
    ensure_dirs()
    writers = OFFLINE_WRITERS if args.writer == "offline" else [args.writer]
    for w in writers:
        name = w if w != "claude" else f"claude_{args.prompt.removesuffix('.md')}"
        rows = generate(w, args.prompt)
        path = RUNS_DIR / f"{name}.jsonl"
        path.write_text("\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf-8")
        print(f"{name}: {len(rows)} briefs -> {path}")


if __name__ == "__main__":
    main()
