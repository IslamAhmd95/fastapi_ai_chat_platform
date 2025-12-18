import os
from sqlmodel import Session, select
from src.models.user import User
from src.core.hashing import hash_password
from src.core.database import engine


def seed_admin_user(db: Session) -> User | None:

    required_vars = [
        "ADMIN_EMAIL",
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD",
        "ADMIN_NAME",
    ]

    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing admin env vars: {', '.join(missing)}")

    admin_email = os.getenv("ADMIN_EMAIL")
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")
    admin_name = os.getenv("ADMIN_NAME")

    existing_user = db.scalar(
        select(User).where(
            (User.email == admin_email) | (User.username == admin_username)
        )
    )

    if existing_user:
        if not existing_user.is_unlimited:
            existing_user.is_unlimited = True
            db.add(existing_user)
            db.commit()
            db.refresh(existing_user)
        return existing_user

    # Create new admin user
    admin_user = User(
        email=admin_email,
        username=admin_username,
        name=admin_name,
        password=hash_password(admin_password),
        is_unlimited=True,
        ai_requests_count=0
    )

    try:
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        return admin_user
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to seed admin user: {str(e)}")


if __name__ == "__main__":

    if os.getenv("ENABLE_DEV_SEEDER") != "true":
        raise RuntimeError("Seeder is disabled in this environment")
    
    with Session(engine) as db:
        admin = seed_admin_user(db)
        if admin:
            print(f"Admin user seeded successfully: {admin.email}")
        else:
            print("Admin user already exists")

