"""Builds the test harness and judges a submission against all test cases."""
from app.judge0 import run_code


def build_program(user_code: str, function_name: str) -> str:
    """Wrap the player's function with a stdin-reading harness."""
    harness = (
        "\n\n"
        "import sys\n"
        "def _main():\n"
        "    _data = sys.stdin.read().split()\n"
        f"    _args = [int(x) for x in _data]\n"
        f"    print({function_name}(*_args))\n"
        "_main()\n"
    )
    return user_code + harness


def judge_submission(user_code: str, problem) -> dict:
    """Run user_code against every test case of a problem. Returns a verdict."""
    full_program = build_program(user_code, problem.function_name)

    total = len(problem.test_cases)
    passed = 0
    first_failure = None

    for tc in problem.test_cases:
        result = run_code(full_program, tc.input_data, problem.time_limit_sec)
        status = result.get("status", {}).get("description", "Unknown")
        actual = (result.get("stdout") or "").strip()
        expected = tc.expected_output.strip()

        if status == "Accepted" and actual == expected:
            passed += 1
        elif first_failure is None:
            first_failure = {
                "input": tc.input_data,
                "expected": expected,
                "actual": actual,
                "status": status,
                "is_hidden": tc.is_hidden,
            }

    all_passed = passed == total
    return {
        "all_passed": all_passed,
        "passed": passed,
        "total": total,
        "first_failure": first_failure,
    }