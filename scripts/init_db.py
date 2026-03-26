import os
import sys

# Add project root to Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.db.base import Base
from app.db.session import engine

# Import models so metadata is registered
from app.models.user import User  # noqa: F401
from app.models.child import Child  # noqa: F401
from app.models.incident import Incident  # noqa: F401
from app.models.abc_record import ABCRecord  # noqa: F401
from app.models.intervention import Intervention  # noqa: F401
from app.models.prediction import Prediction  # noqa: F401


def main():
    Base.metadata.create_all(bind=engine)
    print("Supabase tables created successfully.")


if __name__ == "__main__":
    main()