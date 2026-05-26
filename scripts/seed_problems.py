"""Seed script — inserts starter problems into the database. Safe to re-run."""
from app.database import SessionLocal
from app.models import Problem, TestCase


def seed():
    db = SessionLocal()
    try:
        slug = "sum-two-integers"

        # Don't duplicate if it already exists
        if db.query(Problem).filter(Problem.slug == slug).first():
            print(f"Problem '{slug}' already exists, skipping.")
            return

        problem = Problem(
            slug=slug,
            title="Sum of Two Integers",
            statement=(
                "Write a function `add` that takes two integers `a` and `b` "
                "and returns their sum.\n\n"
                "Example: add(3, 5) should return 8."
            ),
            difficulty="easy",
            function_name="add",
            starter_code="def add(a, b):\n    # your code here\n    pass\n",
            reference_solution="def add(a, b):\n    return a + b\n",
            time_limit_sec=2,
            memory_limit_mb=128,
        )

        problem.test_cases = [
            TestCase(input_data="3 5", expected_output="8", is_hidden=False),
            TestCase(input_data="0 0", expected_output="0", is_hidden=False),
            TestCase(input_data="-4 10", expected_output="6", is_hidden=True),
            TestCase(input_data="100 -250", expected_output="-150", is_hidden=True),
            TestCase(input_data="-7 -8", expected_output="-15", is_hidden=True),
        ]

        db.add(problem)
        db.commit()
        print(f"Seeded problem '{slug}' with {len(problem.test_cases)} test cases.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()