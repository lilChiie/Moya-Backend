from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime

from api.extensions import db
from models.user import User
from models.destination import Destination
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


# POST /api/clean-reports  — User melaporkan destinasi sudah bersih
@clean_reports_bp.route("", methods=["POST"])
@jwt_required()
def create_clean_report():
    user_id = int(get_jwt_identity())

    destination_id = request.form.get("destination_id")
    notes = request.form.get("notes")
    image_url = request.files.get("image_url")

    # Validasi
    if not destination_id:
        return jsonify({
            "success": False,
            "message": "destination_id is required"
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

    # Cek relasi user & destination
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

    # Simpan gambar
    original_filename = secure_filename(image_url.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{timestamp}_{original_filename}"
    image_path = UPLOAD_FOLDER / filename

    image_url.save(image_path)

    try:
        clean_report = CleanReport(
            user_id=user_id,
            destination_id=destination_id,
            image_url=f"/static/uploads/clean_reports/{filename}",
            notes=notes,
            status="pending"
        )
        db.session.add(clean_report)
        db.session.flush()

        # Notifikasi ke user: laporan diterima
        notif_user = Notification(
            user_id=user_id,
            title="Laporan Kebersihan Dikirim",
            description=(
                f"Laporan kebersihan untuk destinasi "
                f"\"{destination.name}\" berhasil dikirim "
                f"dan sedang menunggu verifikasi admin."
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
                    f"\"{destination.name}\" sudah bersih. "
                    f"Silakan verifikasi laporan ini."
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
    status_filter = request.args.get("status")

    query = CleanReport.query.order_by(CleanReport.created_at.desc())

    if status_filter:
        query = query.filter_by(status=status_filter)

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


# PUT /api/clean-reports/<id>/verify  — Admin verifikasi laporan
@clean_reports_bp.route("/<int:report_id>/verify", methods=["PUT"])
@jwt_required()
def verify_clean_report(report_id):
    """
    Admin memverifikasi laporan kebersihan.
    JSON body:
        - status      (required): "verified" atau "rejected"
        - admin_notes (optional): catatan admin
    
    Ketika status diubah ke "verified":
        - cleanliness_status destinasi kembali ke default ("Safe")
        - Nanti bagian DSS akan memproses perubahan poin (bukan scope API ini)
    """
    user_id = int(get_jwt_identity())
    admin = User.query.get(user_id)

    if not admin or admin.role != 'admin':
        return jsonify({
            "success": False,
            "message": "Only admin can verify reports"
        }), 403

    report = CleanReport.query.get(report_id)
    if not report:
        return jsonify({
            "success": False,
            "message": "Clean report not found"
        }), 404

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")

    if new_status not in ("verified", "rejected"):
        return jsonify({
            "success": False,
            "message": "Status must be 'verified' or 'rejected'"
        }), 400

    try:
        report.status = new_status
        report.admin_notes = data.get("admin_notes", report.admin_notes)

        if new_status == "verified":
            report.verified_at = datetime.utcnow()

            # Reset cleanliness_status destinasi ke default ("Safe")
            destination = Destination.query.get(report.destination_id)
            if destination:
                destination.cleanliness_status = "Safe"
                destination.cleanliness_score = 0.5000

        db.session.flush()

        # ── Notifikasi ke user pelapor ────────────
        if new_status == "verified":
            notif_msg = (
                f"Laporan kebersihan Anda untuk destinasi "
                f"\"{report.destination.name}\" telah diverifikasi oleh admin. "
                f"Terima kasih atas kontribusi Anda!"
            )
        else:
            notif_msg = (
                f"Laporan kebersihan Anda untuk destinasi "
                f"\"{report.destination.name}\" ditolak oleh admin."
            )
            if data.get("admin_notes"):
                notif_msg += f" Catatan: {data['admin_notes']}"

        notif = Notification(
            user_id=report.user_id,
            title="Update Laporan Kebersihan",
            description=notif_msg
        )
        db.session.add(notif)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Clean report {new_status} successfully",
            "data": report.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": "Failed to verify clean report",
            "error": str(e)
        }), 500
