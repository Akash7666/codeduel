"""Builds the test harness and judges a submission against all test cases."""
from app.judge0 import run_code
import json

def build_program(user_code: str, function_name: str) -> str:
    """Wrap the player's function with a JSON-based stdin harness.

    Suppresses the user's own stdout so only the JSON return value is judged.
    """
    harness = (
        "\n\n"
        "import sys, json, io\n"
        "def _main():\n"
        "    _args = json.loads(sys.stdin.read())\n"
        "    _real_stdout = sys.stdout\n"
        "    sys.stdout = io.StringIO()\n"  # swallow user prints
        f"    _result = {function_name}(*_args)\n"
        "    sys.stdout = _real_stdout\n"   # restore for our output
        "    print(json.dumps(_result))\n"
        "_main()\n"
    )
    return user_code + harness






def judge_submission(user_code: str, problem) -> dict:
    """Run user_code against every test case. Returns per-case results too."""
    full_program = build_program(user_code, problem.function_name)

    total = len(problem.test_cases)
    passed = 0
    first_failure = None
    case_results = []

    for idx, tc in enumerate(problem.test_cases):
        result = run_code(full_program, tc.input_data, problem.time_limit_sec)
        status = result.get("status", {}).get("description", "Unknown")
        actual_raw = (result.get("stdout") or "").strip()

        match = False
        if status == "Accepted":
            try:
                match = json.loads(actual_raw) == json.loads(tc.expected_output)
            except (json.JSONDecodeError, ValueError):
                match = actual_raw == tc.expected_output.strip()

        if match:
            passed += 1
        elif first_failure is None:
            first_failure = {
                "input": tc.input_data,
                "expected": tc.expected_output,
                "actual": actual_raw,
                "status": status,
                "is_hidden": tc.is_hidden,
            }

        # Per-case result. For hidden cases we don't expose input/output.
        case_results.append({
            "index": idx + 1,
            "is_hidden": tc.is_hidden,
            "passed": match,
            "status": status,
            # Only include details for visible cases
            "input": None if tc.is_hidden else tc.input_data,
            "expected": None if tc.is_hidden else tc.expected_output,
            "actual": None if tc.is_hidden else actual_raw,
        })

    return {
        "all_passed": passed == total,
        "passed": passed,
        "total": total,
        "first_failure": first_failure,
        "case_results": case_results,
    }