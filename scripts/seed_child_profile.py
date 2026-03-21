from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.models.child import Child
from app.services.graph_memory_service import create_child_profile_node


def main():
    db: Session = SessionLocal()

    try:
        user = User(
            email="parent1@example.com",
            full_name="Demo Parent"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        child = Child(
            parent_id=user.id,
            name="Aarav",
            nickname="Aru",
            age_years=6,
            sensory_triggers="Loud noises, crowded spaces, transitions",
            calming_strategies="Deep pressure hug, favorite toy, quiet corner",
            school_notes="Gets overwhelmed after long school days",
            medical_notes="No formal diagnosis yet"
        )
        db.add(child)
        db.commit()
        db.refresh(child)

        create_child_profile_node(
            child_id=child.id,
            child_name=child.name,
            parent_id=child.parent_id,
        )

        print("Demo user and child profile seeded successfully.")
        print(f"User ID: {user.id}")
        print(f"Child ID: {child.id}")

    finally:
        db.close()


if __name__ == "__main__":
    main()