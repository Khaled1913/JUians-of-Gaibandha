from app import app
from models import Information
from sqlalchemy import or_


with app.app_context():

    keyword = "%Computer%"

    members = Information.query.filter(
        Information.status == "Approved",
        or_(
            Information.full_name.ilike(keyword),
            Information.department.ilike(keyword),
            Information.batch.ilike(keyword),
            Information.session.ilike(keyword),
            Information.phone.ilike(keyword),
            Information.email.ilike(keyword),
            Information.student_id.ilike(keyword),
            Information.registration_no.ilike(keyword)
        )
    ).all()


    print("\n==============================")
    print("SEARCH TEST")
    print("==============================")

    print("Found:", len(members))

    for member in members:

        print(
            member.id,
            "|",
            member.full_name,
            "|",
            member.department,
            "|",
            member.status
        )

    print("==============================")
    