"""Seed script — inserts starter problems into the database. Safe to re-run."""
from app.database import SessionLocal
from app.models import Problem, TestCase


def seed():
    db = SessionLocal()
    try:
        problems_data = [
            {
                "slug": "sum-two-integers",
                "title": "Sum of Two Integers",
                "difficulty": "easy",
                "function_name": "add",
                "statement": (
                    "Write a function `add(a, b)` that takes two integers and "
                    "returns their sum.\n\nExample: add(3, 5) returns 8."
                ),
                "starter_code": "def add(a, b):\n    # your code here\n    pass\n",
                "reference_solution": "def add(a, b):\n    return a + b\n",
                "tests": [
                    ("[3, 5]", "8", False),
                    ("[0, 0]", "0", False),
                    ("[-4, 10]", "6", True),
                    ("[100, -250]", "-150", True),
                    ("[-7, -8]", "-15", True),
                ],
            },
            {
                "slug": "reverse-string",
                "title": "Reverse a String",
                "difficulty": "easy",
                "function_name": "reverse_string",
                "statement": (
                    "Write a function `reverse_string(s)` that returns the string "
                    "`s` reversed.\n\nExample: reverse_string(\"hello\") returns \"olleh\"."
                ),
                "starter_code": "def reverse_string(s):\n    # your code here\n    pass\n",
                "reference_solution": "def reverse_string(s):\n    return s[::-1]\n",
                "tests": [
                    ('["hello"]', '"olleh"', False),
                    ('["a"]', '"a"', False),
                    ('[""]', '""', True),
                    ('["racecar"]', '"racecar"', True),
                    ('["CodeDuel"]', '"leuDedoC"', True),
                ],
            },
            {
                "slug": "pair-sum",
                "title": "Pair Sum",
                "difficulty": "medium",
                "function_name": "pair_sum",
                "statement": (
                    "Given a list of integers `nums` and an integer `target`, return "
                    "the indices of the two numbers that add up to `target`, as a list "
                    "`[i, j]` with i < j. Exactly one solution exists.\n\n"
                    "Example: pair_sum([2, 7, 11, 15], 9) returns [0, 1]."
                ),
                "starter_code": "def pair_sum(nums, target):\n    # your code here\n    pass\n",
                "reference_solution": (
                    "def pair_sum(nums, target):\n"
                    "    seen = {}\n"
                    "    for i, n in enumerate(nums):\n"
                    "        if target - n in seen:\n"
                    "            return [seen[target - n], i]\n"
                    "        seen[n] = i\n"
                ),
                "tests": [
                    ("[[2, 7, 11, 15], 9]", "[0, 1]", False),
                    ("[[3, 2, 4], 6]", "[1, 2]", False),
                    ("[[3, 3], 6]", "[0, 1]", True),
                    ("[[1, 5, 8, 3], 11]", "[2, 3]", True),
                    ("[[-1, -2, -3, -4], -7]", "[2, 3]", True),
                ],
            },
            {
                "slug": "longest-run",
                "title": "Longest Run",
                "difficulty": "hard",
                "function_name": "longest_run",
                "statement": (
                    "Given a list of integers `nums`, return the length of the longest "
                    "run of consecutive equal values.\n\n"
                    "Example: longest_run([1, 1, 2, 2, 2, 3]) returns 3."
                ),
                "starter_code": "def longest_run(nums):\n    # your code here\n    pass\n",
                "reference_solution": (
                    "def longest_run(nums):\n"
                    "    if not nums:\n"
                    "        return 0\n"
                    "    best = run = 1\n"
                    "    for i in range(1, len(nums)):\n"
                    "        run = run + 1 if nums[i] == nums[i-1] else 1\n"
                    "        best = max(best, run)\n"
                    "    return best\n"
                ),
                "tests": [
                    ("[[1, 1, 2, 2, 2, 3]]", "3", False),
                    ("[[5]]", "1", False),
                    ("[[]]", "0", True),
                    ("[[4, 4, 4, 4]]", "4", True),
                    ("[[1, 2, 3, 4, 5]]", "1", True),
                    ("[[7, 7, 1, 7, 7, 7]]", "3", True),
                ],
            },
        ]

        for pd in problems_data:
            if db.query(Problem).filter(Problem.slug == pd["slug"]).first():
                print(f"Problem '{pd['slug']}' already exists, skipping.")
                continue
            problem = Problem(
                slug=pd["slug"],
                title=pd["title"],
                statement=pd["statement"],
                difficulty=pd["difficulty"],
                function_name=pd["function_name"],
                starter_code=pd["starter_code"],
                reference_solution=pd["reference_solution"],
                time_limit_sec=2,
                memory_limit_mb=128,
            )
            problem.test_cases = [
                TestCase(input_data=inp, expected_output=out, is_hidden=hidden)
                for (inp, out, hidden) in pd["tests"]
            ]
            db.add(problem)
            print(f"Seeded '{pd['slug']}' ({pd['difficulty']}) with {len(pd['tests'])} tests.")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()