from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime
from decimal import Decimal

from api.models import db, Report, User, Destination
from api.ai.yolo import analyze_photo_for_trash


reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


UPLOAD_FOLDER = Path("uploads/reports")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def report_to_dict(report):
    return {
        "id": report.id,
        "user_id": report.user_id,
        "destination_id": report.destination_id,
        "image_url": report.image_url,
        "user_notes": report.user_notes,
        "admin_notes": report.admin_notes,
        "status": report.status,
        "detected_count": report.detected_count,
        "score": float(report.score),
        "created_at": (
            report.created_at.isoformat()
            if report.created_at
            else None
        ),
        "updated_at": (
            report.updated_at.isoformat()
            if report.updated_at
            else None
        ),
    }


@reports_bp.route("", methods=["GET"])
def get_reports():

    reports = Report.query.order_by(Report.created_at.desc()).all()

    return jsonify({
        "success": True,
        "data": [report_to_dict(report) for report in reports]
    }), 200

@reports_bp.route("/<int:report_id>", methods=["GET"])
def get_report(report_id):

    report = Report.query.get(report_id)

    if not report:
        return jsonify({
            "success": False,
            "message": "Report not found"
        }), 404

    return jsonify({
        "success": True,
        "data": report_to_dict(report)
    }), 200


@reports_bp.route("", methods=["POST"])
def create_report():

    user_id = request.form.get("user_id")
    destination_id = request.form.get("destination_id")
    user_notes = request.form.get("user_notes")

    image = request.files.get("image")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "user_id is required"
        }), 400

    if not destination_id:
        return jsonify({
            "success": False,
            "message": "destination_id is required"
        }), 400

    if not image:
        return jsonify({
            "success": False,
            "message": "Image is required"
        }), 400

    if image.filename == "":
        return jsonify({
            "success": False,
            "message": "Image filename is empty"
        }), 400

    if not allowed_file(image.filename):
        return jsonify({
            "success": False,
            "message": "Only JPG, JPEG, PNG, and WEBP images are allowed"
        }), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    destination = Destination.query.get(destination_id)

    if not destination:
        return jsonify({
            "success": False,
            "message": "Destination not found"
        }), 404

    original_filename = secure_filename(image.filename)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    filename = f"{timestamp}_{original_filename}"

    image_path = UPLOAD_FOLDER / filename

    image.save(image_path)

    try:

        yolo_result = analyze_photo_for_trash(str(image_path))

        detected_count = yolo_result["detected_count"]
        score = yolo_result["score"]

        report = Report(
            user_id=user_id,
            destination_id=destination_id,
            image_url=f"/uploads/reports/{filename}",
            user_notes=user_notes,
            status="pending",
            detected_count=detected_count,
            score=score
        )

        db.session.add(report)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Report created successfully",
            "data": report_to_dict(report)
        }), 201

    except Exception as e:

        db.session.rollback()

    
        if image_path.exists():
            image_path.unlink()

        return jsonify({
            "success": False,
            "message": "Failed to process report",
            "error": str(e)
        }), 500

@reports_bp.route("/<int:report_id>", methods=["PUT"])
def update_report(report_id):

    report = Report.query.get(report_id)

    if not report:
        return jsonify({
            "success": False,
            "message": "Report not found"
        }), 404

    data = request.get_json(silent=True) or {}

    
    if "user_notes" in data:
        report.user_notes = data["user_notes"]

    if "admin_notes" in data:
        report.admin_notes = data["admin_notes"]

  
    if "status" in data:

        allowed_status = {
            "pending",
            "resolved"
        }

        if data["status"] not in allowed_status:
            return jsonify({
                "success": False,
                "message": "Invalid status"
            }), 400

        report.status = data["status"]

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Report updated successfully",
        "data": report_to_dict(report)
    }), 200


@reports_bp.route("/<int:report_id>", methods=["DELETE"])
def delete_report(report_id):

    report = Report.query.get(report_id)

    if not report:
        return jsonify({
            "success": False,
            "message": "Report not found"
        }), 404

    db.session.delete(report)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Report deleted successfully"
    }), 200

@reports_bp.route("/latest", methods=["GET"])
def get_latest_reports():

    try:
        limit = request.args.get("limit", 5, type=int)

        if limit <= 0:
            return jsonify({
                "success": False,
                "message": "Limit must be greater than 0"
            }), 400

        # Batasi agar tidak terlalu banyak data
        limit = min(limit, 5)

        reports = (
            Report.query
            .order_by(Report.created_at.desc())
            .limit(limit)
            .all()
        )

        return jsonify({
            "success": True,
            "data": [
                report_to_dict(report)
                for report in reports
            ]
        }), 200

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Failed to get latest reports",
            "error": str(e)
        }), 500