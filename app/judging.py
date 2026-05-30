"""Builds the test harness and judges a submission against all test cases."""
from app.judge0 import run_code
import json

def build_program(user_code: str, function_name: str) -> str:
    """Wrap the player's function with a JSON-based stdin harness.

    Reads a JSON array of arguments from stdin, calls the function with them,
    and prints the result as JSON.
    """
    harness = (
        "\n\n"
        "import sys, json\n"
        "def _main():\n"
        "    _args = json.loads(sys.stdin.read())\n"
        f"    _result = {function_name}(*_args)\n"
        "    print(json.dumps(_result))\n"
        "_main()\n"
    )
    return user_code + harness




def judge_submission(user_code: str, problem) -> dict:
    """Run user_code against every test case. Compares JSON-decoded values."""
    full_program = build_program(user_code, problem.function_name)

    total = len(problem.test_cases)
    passed = 0
    first_failure = None

    for tc in problem.test_cases:
        result = run_code(full_program, tc.input_data, problem.time_limit_sec)
        status = result.get("status", {}).get("description", "Unknown")
        actual_raw = (result.get("stdout") or "").strip()

        # Compare decoded JSON values so formatting differences don't matter.
        match = False
        if status == "Accepted":
            try:
                match = json.loads(actual_raw) == json.loads(tc.expected_output)
            except (json.JSONDecodeError, ValueError):
                match = actual_raw == tc.expected_output.strip()  # fallback

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

    return {
        "all_passed": passed == total,
        "passed": passed,
        "total": total,
        "first_failure": first_failure,
    }