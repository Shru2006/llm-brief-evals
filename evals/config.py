"""Paths and settings shared by every eval script."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
PROMPTS_DIR = ROOT / "prompts"

GOLDEN_PATH = DATA_DIR / "golden_leads.jsonl"
METRICS_PATH = REPORTS_DIR / "metrics.json"
SCORECARD_PATH = REPORTS_DIR / "scorecard.md"

SEED = 42
MAX_WORDS = 120

# Release gate: a candidate prompt or model ships only if it clears both bars.
GATE_MIN_PASS_RATE = 0.90          # share of briefs passing every check
GATE_MAX_COMPLIANCE_FAIL = 0.01    # share with a promise or protected-attribute breach

# Live mode only (needs Anthropic credentials). Offline runs never call the API.
LLM_MODEL = "claude-opus-5-5"


def ensure_dirs() -> None:
    for d in (DATA_DIR, RUNS_DIR, REPORTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
