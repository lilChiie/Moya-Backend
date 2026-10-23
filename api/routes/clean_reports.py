from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from pathlib import Path

from api.extensions import db
from api.utils import now_wib
from api.models import Report
from models.user import User
from models.clean_report import CleanReport
from models.notification import Notification


clean_reports_bp = Blueprint('clean_reports', __name__)


UPLOAD_FOLDER = Path("static/uploads/clean_reports")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# POST /api/clean-reports  — User me-reply laporan kotor dengan bukti kebersihan
@clean_reports_bp.route("", methods=["POST"])
@jwt_required()
def create_clean_report():
    user_id = int(get_jwt_identity())

    report_id = request.form.get("report_id")
    notes = request.form.get("notes")
    image_url = request.files.get("image_url")

    # Validasi
    if not report_id:
        return jsonify({
            "success": False,
            "message": "report_id is required"
        }), 400

    if not image_url:
        return jsonify({
            "success": False,
            "message": "image_url is required"
        }), 400

    if image_url.filename == "":
        return jsonify({
            "success": False,
            "message": "Image filename is empty"
        }), 400

    if not allowed_file(image_url.filename):
        return jsonify({
            "success": False,
            "message": "Only JPG, JPEG, PNG, and WEBP images are allowed"
        }), 400

    # Cek relasi user & report
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    report = Report.query.get(report_id)
    if not report:
        return jsonify({
            "success": False,
            "message": "Report not found"
        }), 404

    # Simpan gambar
    original_filename = secure_filename(image_url.filename)
    timestamp = now_wib().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{timestamp}_{original_filename}"
    image_path = UPLOAD_FOLDER / filename

    image_url.save(image_path)

    try:
        clean_report = CleanReport(
            user_id=user_id,
            report_id=int(report_id),
            image_url=f"/static/uploads/clean_reports/{filename}",
            notes=notes
        )
        db.session.add(clean_report)
        db.session.flush()

        destination_name = (
            report.destination.name if report.destination else "Unknown"
        )

        # Notifikasi ke user: laporan diterima
        notif_user = Notification(
            user_id=user_id,
            title="Laporan Kebersihan Dikirim",
            description=(
                f"Laporan kebersihan untuk destinasi "
                f"\"{destination_name}\" berhasil dikirim."
            )
        )
        db.session.add(notif_user)

        # Notifikasi ke semua admin
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            notif_admin = Notification(
                user_id=admin.id,
                title="Laporan Kebersihan Baru",
                description=(
                    f"User \"{user.name}\" melaporkan bahwa destinasi "
                    f"\"{destination_name}\" sudah bersih."
                )
            )
            db.session.add(notif_admin)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Clean report submitted successfully",
            "data": clean_report.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()

        # Hapus gambar jika proses gagal
        if image_path.exists():
            image_path.unlink()

        return jsonify({
            "success": False,
            "message": "Failed to submit clean report",
            "error": str(e)
        }), 500


# GET /api/clean-reports  — List semua laporan kebersihan (admin)
@clean_reports_bp.route("", methods=["GET"])
@jwt_required()
def get_clean_reports():
    report_id_filter = request.args.get("report_id")

    query = CleanReport.query.order_by(CleanReport.created_at.desc())

    if report_id_filter:
        query = query.filter_by(report_id=int(report_id_filter))

    reports = query.all()

    return jsonify({
        "success": True,
        "data": [r.to_dict() for r in reports]
    }), 200


# GET /api/clean-reports/my  — Riwayat laporan kebersihan user
@clean_reports_bp.route("/my", methods=["GET"])
@jwt_required()
def get_my_clean_reports():
    user_id = int(get_jwt_identity())

    reports = (
        CleanReport.query
        .filter_by(user_id=user_id)
        .order_by(CleanReport.created_at.desc())
        .all()
    )

    return jsonify({
        "success": True,
        "data": [r.to_dict() for r in reports]
    }), 200


# GET /api/clean-reports/<id>  — Detail laporan kebersihan
@clean_reports_bp.route("/<int:report_id>", methods=["GET"])
@jwt_required()
def get_clean_report(report_id):
    report = CleanReport.query.get(report_id)

    if not report:
        return jsonify({
            "success": False,
            "message": "Clean report not found"
        }), 404

    return jsonify({
        "success": True,
        "data": report.to_dict()
    }), 200


# GET /api/clean-reports/by-report/<report_id>  — Semua laporan bersih untuk 1 laporan kotor
@clean_reports_bp.route("/by-report/<int:dirty_report_id>", methods=["GET"])
@jwt_required()
def get_clean_reports_by_report(dirty_report_id):
    report = Report.query.get(dirty_report_id)
    if not report:
        return jsonify({
            "success": False,
            "message": "Report not found"
        }), 404

    clean_reports = (
        CleanReport.query
        .filter_by(report_id=dirty_report_id)
        .order_by(CleanReport.created_at.desc())
        .all()
    )

    return jsonify({
        "success": True,
        "report_id": dirty_report_id,
        "destination_name": report.destination.name if report.destination else None,
        "total_clean_reports": len(clean_reports),
        "data": [r.to_dict() for r in clean_reports]
    }), 200
