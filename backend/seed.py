from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    if not User.query.filter_by(username="admin").first():
        db.session.add(User(username="admin", email="admin@example.com"))
        db.session.commit()
    print("seed done")
