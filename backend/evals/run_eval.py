"""
Reproducible Arabic evaluation harness for the Nagham AI agent.

Runs every case in dataset.jsonl against the live agent (using the real dev
database, read-only — no rows are created/modified/deleted) and produces a
JSON results file plus a markdown summary.

Usage:
    venv/Scripts/python.exe evals/run_eval.py --label baseline
    venv/Scripts/python.exe evals/run_eval.py --label after-phase1 --compare baseline
"""

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.connection import SessionLocal
from app.ai.agent import run_nagham_agent

EVALS_DIR = Path(__file__).resolve().parent

# --- Adapter seam -----------------------------------------------------------
# Before Phase 1 (M2), the agent has no concept of conversation history, so
# follow-up turns are sent in isolation. After M2 wires history support into
# run_nagham_agent / the graph, flip USE_HISTORY and extend the call below.
USE_HISTORY = True


def call_agent(db, message: str, history: list) -> dict:
    if USE_HISTORY:
        return run_nagham_agent(db, message, limit=10, history=history)
    return run_nagham_agent(db, message, limit=10)


# --- Scoring -----------------------------------------------------------------

def score_turn(expected: dict, result: dict | None, error: str | None) -> dict:
    checks = {}

    if error is not None:
        checks["ran_without_error"] = False
        return {"checks": checks, "passed": False}

    checks["ran_without_error"] = True

    found_songs = result.get("results", []) if result else []
    found_ids = [item["song"].id for item in found_songs]
    found_titles = {item["song"].title for item in found_songs}
    found_artists = {
        item["song"].artist.name_ar
        for item in found_songs
        if item["song"].artist
    }
    analysis = (result or {}).get("analysis", {}) or {}

    if "expected_song_ids" in expected:
        checks["exact_song_set"] = set(found_ids) == set(expected["expected_song_ids"])

    if "expected_song_ids_subset_of" in expected:
        allowed = set(expected["expected_song_ids_subset_of"])
        checks["subset_and_nonempty"] = (
            len(found_ids) > 0 and set(found_ids) <= allowed
        )

    if "expected_top1" in expected:
        checks["top1_match"] = bool(found_ids) and found_ids[0] == expected["expected_top1"]

    if "expected_result_count_max" in expected:
        checks["result_count_within_max"] = len(found_ids) <= expected["expected_result_count_max"]

    if "expected_difficulty" in expected:
        checks["difficulty_match"] = analysis.get("difficulty") == expected["expected_difficulty"]

    if "expected_exclude_artist" in expected:
        checks["artist_excluded"] = expected["expected_exclude_artist"] not in found_artists

    if "expect_empty" in expected:
        checks["is_empty_as_expected"] = (len(found_ids) == 0) == expected["expect_empty"]

    if "expect_no_crash" in expected:
        checks["no_crash"] = True

    if "expected_intent" in expected:
        checks["intent_match"] = analysis.get("intent") == expected["expected_intent"]

    # Generic hallucination guard: every DB song title mentioned in the
    # free-text answer must belong to the actual returned result set.
    answer_text = (result or {}).get("answer", "") or ""
    all_db_titles = ALL_SONG_TITLES
    mentioned = {t for t in all_db_titles if t and t in answer_text}
    leaked = mentioned - found_titles
    checks["no_hallucinated_titles"] = len(leaked) == 0
    if leaked:
        checks["_leaked_titles"] = sorted(leaked)

    meaningful = {k: v for k, v in checks.items() if not k.startswith("_") and isinstance(v, bool)}
    passed = all(meaningful.values()) if meaningful else True

    return {"checks": checks, "passed": passed, "found_ids": found_ids}


def load_all_song_titles(db) -> set[str]:
    from app.models.song import Song
    return {s.title for s in db.query(Song.title).all() or db.query(Song).all()}


def run_dataset(label: str) -> dict:
    dataset_path = EVALS_DIR / "dataset.jsonl"
    cases = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    db = SessionLocal()
    global ALL_SONG_TITLES
    from app.models.song import Song
    ALL_SONG_TITLES = {s.title for s in db.query(Song).all()}

    all_results = []
    latencies = []

    for case in cases:
        case_id = case["id"]
        category = case["category"]
        history = []
        turn_results = []

        for turn in case["turns"]:
            message = turn["input"]
            expected = turn.get("expected", {})

            start = time.perf_counter()
            error = None
            result = None
            try:
                result = call_agent(db, message, history)
            except Exception as exc:  # noqa: BLE001 - eval harness must not crash on bad cases
                error = f"{type(exc).__name__}: {exc}"
                traceback.print_exc()
            elapsed = time.perf_counter() - start
            latencies.append(elapsed)

            scored = score_turn(expected, result, error)
            scored["input"] = message
            scored["error"] = error
            scored["latency_s"] = round(elapsed, 3)
            turn_results.append(scored)

            history.append({
                "role": "user",
                "content": message,
            })
            if result:
                history.append({
                    "role": "assistant",
                    "content": result.get("answer", ""),
                    "analysis": result.get("analysis"),
                    "result_ids": [item["song"].id for item in result.get("results", [])],
                })

        case_passed = all(t["passed"] for t in turn_results)
        all_results.append({
            "id": case_id,
            "category": category,
            "passed": case_passed,
            "turns": turn_results,
        })

    db.close()

    by_category: dict[str, list[bool]] = {}
    for r in all_results:
        by_category.setdefault(r["category"], []).append(r["passed"])

    category_summary = {
        cat: {"passed": sum(v), "total": len(v), "rate": round(sum(v) / len(v), 2)}
        for cat, v in sorted(by_category.items())
    }

    overall_rate = round(sum(r["passed"] for r in all_results) / len(all_results), 3)
    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0

    summary = {
        "label": label,
        "total_cases": len(all_results),
        "overall_pass_rate": overall_rate,
        "category_summary": category_summary,
        "latency_mean_s": round(sum(latencies) / len(latencies), 3) if latencies else 0,
        "latency_p50_s": round(p50, 3),
        "latency_p95_s": round(p95, 3),
    }

    output = {"summary": summary, "results": all_results}

    results_path = EVALS_DIR / f"results_{label}.json"
    results_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    write_markdown_report(label, summary, all_results)

    return output


def write_markdown_report(label: str, summary: dict, all_results: list) -> None:
    lines = [
        f"# Nagham AI eval run — `{label}`",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Overall pass rate: {summary['overall_pass_rate']:.0%}",
        f"- Latency: mean {summary['latency_mean_s']}s, p50 {summary['latency_p50_s']}s, p95 {summary['latency_p95_s']}s",
        "",
        "## By category",
        "",
        "| Category | Passed | Total | Rate |",
        "|---|---|---|---|",
    ]
    for cat, stats in summary["category_summary"].items():
        lines.append(f"| {cat} | {stats['passed']} | {stats['total']} | {stats['rate']:.0%} |")

    lines += ["", "## Failing cases", ""]
    failing = [r for r in all_results if not r["passed"]]
    if not failing:
        lines.append("None.")
    else:
        for r in failing:
            lines.append(f"### `{r['id']}` ({r['category']})")
            for t in r["turns"]:
                status = "PASS" if t["passed"] else "FAIL"
                lines.append(f"- [{status}] input: {t['input']!r}")
                if t["error"]:
                    lines.append(f"  - error: {t['error']}")
                else:
                    failed_checks = {k: v for k, v in t["checks"].items() if v is False}
                    if failed_checks:
                        lines.append(f"  - failed checks: {failed_checks}")
                    lines.append(f"  - found_ids: {t.get('found_ids')}")
            lines.append("")

    report_path = EVALS_DIR / f"{label}_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="baseline")
    args = parser.parse_args()

    out = run_dataset(args.label)
    print(json.dumps(out["summary"], ensure_ascii=False, indent=2))
