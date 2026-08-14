# ==========================================
# routes/api.py
# JUians of Gaibandha Portal
# API Routes
# ==========================================


from flask import (
    Blueprint,
    jsonify,
    request
)

from sqlalchemy import or_

from models import Information

from services.member_service import (
    get_member_statistics
)



# ==========================================
# Blueprint
# ==========================================

api_bp = Blueprint(
    "api",
    __name__,
    url_prefix="/api"
)





# ==========================================
# Get All Approved Members
# ==========================================

@api_bp.route(
    "/members",
    methods=["GET"]
)
def get_members():


    members = Information.query.filter_by(
        status="Approved"
    ).order_by(
        Information.created_at.desc()
    ).all()



    data = []



    for member in members:


        data.append({

            "id": member.id,

            "name": member.full_name,

            "category": member.category,

            "department": member.department,

            "session": member.session,

            "phone": member.phone,

            "email": member.email,

            "occupation": member.occupation,

            "company": member.company,

            "designation": member.designation,

            "photo": member.photo

        })



    return jsonify({

        "success": True,

        "total": len(data),

        "members": data

    })





# ==========================================
# Single Member Details
# ==========================================

@api_bp.route(
    "/member/<int:id>",
    methods=["GET"]
)
def get_member(id):


    member = Information.query.filter_by(

        id=id,

        status="Approved"

    ).first()



    if not member:


        return jsonify({

            "success": False,

            "message": "Member not found"

        }),404



    return jsonify({

        "success": True,

        "member": {


            "id": member.id,

            "name": member.full_name,

            "category": member.category,

            "department": member.department,

            "session": member.session,

            "student_id": member.student_id,

            "phone": member.phone,

            "email": member.email,

            "blood_group": member.blood_group,

            "gender": member.gender,

            "address": member.present_address,

            "occupation": member.occupation,

            "company": member.company,

            "designation": member.designation,

            "facebook": member.facebook,

            "linkedin": member.linkedin,

            "github": member.github,

            "photo": member.photo

        }

    })





# ==========================================
# Search API
# ==========================================

@api_bp.route(
    "/search",
    methods=["GET"]
)
def search_api():


    keyword = request.args.get(
        "q",
        ""
    ).strip()



    if not keyword:


        return jsonify({

            "success": False,

            "message": "Search keyword required"

        })



    search_text = f"%{keyword}%"



    members = Information.query.filter(

        Information.status == "Approved",

        or_(

            Information.full_name.ilike(
                search_text
            ),

            Information.department.ilike(
                search_text
            ),

            Information.phone.ilike(
                search_text
            ),

            Information.email.ilike(
                search_text
            ),

            Information.session.ilike(
                search_text
            )

        )

    ).all()



    result = []



    for member in members:


        result.append({

            "id": member.id,

            "name": member.full_name,

            "department": member.department,

            "session": member.session,

            "phone": member.phone

        })



    return jsonify({

        "success": True,

        "count": len(result),

        "results": result

    })





# ==========================================
# Category API
# ==========================================

@api_bp.route(
    "/category/<category>",
    methods=["GET"]
)
def category_api(category):


    members = Information.query.filter_by(

        category=category,

        status="Approved"

    ).all()



    data = []



    for member in members:


        data.append({

            "id": member.id,

            "name": member.full_name,

            "department": member.department,

            "session": member.session

        })



    return jsonify({

        "success": True,

        "category": category,

        "total": len(data),

        "members": data

    })





# ==========================================
# Statistics API
# ==========================================

@api_bp.route(
    "/statistics",
    methods=["GET"]
)
def statistics_api():


    statistics = get_member_statistics()



    return jsonify({

        "success": True,

        "statistics": statistics

    })





# ==========================================
# Dashboard API
# ==========================================

@api_bp.route(
    "/dashboard",
    methods=["GET"]
)
def dashboard_api():


    stats = get_member_statistics()



    latest_members = Information.query.filter_by(

        status="Approved"

    ).order_by(

        Information.created_at.desc()

    ).limit(5).all()



    members = []



    for member in latest_members:


        members.append({

            "id": member.id,

            "name": member.full_name,

            "category": member.category,

            "department": member.department

        })



    return jsonify({

        "success": True,

        "stats": stats,

        "latest_members": members

    })