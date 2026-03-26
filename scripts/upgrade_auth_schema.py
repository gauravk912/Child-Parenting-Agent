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
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS hashed_password VARCHAR;
        """,
        """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS auth_provider VARCHAR NOT NULL DEFAULT 'local';
        """,
    ]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))

    print("Auth schema upgrade completed successfully.")


if __name__ == "__main__":
    main()