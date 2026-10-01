"""Create the database and safe development seed accounts."""
from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

DEMO_USERS = [
    ("ACC Super Admin", "superadmin@acc.local", "SuperAdmin123!", "super_admin"),
    ("ACC Administrator", "admin@acc.local", "Admin123!", "admin"),
    ("Demo Student", "student@acc.local", "Student123!", "student"),
]


with app.app_context():
    for full_name, email, password, role in DEMO_USERS:
        user = db.session.scalar(db.select(User).where(User.email == email))
        if not user:
            user = User(full_name=full_name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)

    db.session.commit()
    print("Database initialized.")
    print("Demo accounts:")
    for _, email, password, role in DEMO_USERS:
        print(f"  {role:12} {email:28} {password}")
