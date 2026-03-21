from app.db.base import Base
from app.db.session import engine

# Import models so metadata is registered
from app.models import user, child  # noqa: F401


def main():
    Base.metadata.create_all(bind=engine)
    print("Supabase tables created successfully.")


if __name__ == "__main__":
    main()