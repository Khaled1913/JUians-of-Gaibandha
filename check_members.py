from app import app
from models import Information

with app.app_context():

    members = Information.query.all()

    for m in members:
        print(
            m.id,
            "|",
            m.full_name,
            "|",
            repr(m.department),
            "|",
            repr(m.status)
        )