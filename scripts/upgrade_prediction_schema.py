import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import text

from app.db.session import engine


def main():
    statements = [
        """
        ALTER TABLE predictions
        ADD COLUMN IF NOT EXISTS risk_factors TEXT;
        """,
        """
        ALTER TABLE predictions
        ADD COLUMN IF NOT EXISTS prevention_steps TEXT;
        """
    ]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))

    print("Prediction schema upgrade completed successfully.")


if __name__ == "__main__":
    main()