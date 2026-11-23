"""LLM-as-judge (live mode only): catches the paraphrased violations that the
deterministic checks miss. Uses structured outputs so every verdict parses.

The judge is itself evaluated before it is trusted: `python -m evals.meta_eval --judge`
runs it on the labelled fault set and reports its recall and false-positive rate
next to the rule-based checks.
"""
import json

from evals.config import LLM_MODEL, PROMPTS_DIR

RUBRIC = (PROMPTS_DIR / "judge_rubric.md").read_text(encoding="utf-8")

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "unsupported_claim": {"type": "boolean"},
        "promise": {"type": "boolean"},
        "protected_attribute": {"type": "boolean"},
        "usefulness_1_to_5": {"type": "integer"},
        "evidence": {"type": "string"},
    },
    "required": ["unsupported_claim", "promise", "protected_attribute", "usefulness_1_to_5", "evidence"],
    "additionalProperties": False,
}


def judge_brief(payload: dict, brief: str, client=None) -> dict:
    """Return the judge's verdict, plus `flagged` = any rule broken."""
    if client is None:  # pragma: no cover - live only
        import anthropic

        client = anthropic.Anthropic()
    response = client.beta.messages.create(
        model=LLM_MODEL,
        max_tokens=2048,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": VERDICT_SCHEMA}},
        system=RUBRIC,
        messages=[{"role": "user", "content": json.dumps({"payload": payload, "brief": brief})}],
    )
    if response.stop_reason == "refusal":
        return {"error": "refusal", "flagged": True}
    text = next(b.text for b in response.content if b.type == "text")
    verdict = json.loads(text)
    verdict["flagged"] = bool(verdict["unsupported_claim"] or verdict["promise"] or verdict["protected_attribute"])
    verdict["input_tokens"] = getattr(response.usage, "input_tokens", None)
    verdict["output_tokens"] = getattr(response.usage, "output_tokens", None)
    return verdict
