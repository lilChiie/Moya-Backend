from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime, timedelta

from api.models import (
    db,
    Report,
    User,
    Destination
)

from api.ai.yolo import analyze_photo_for_trash


reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/reports"
)



UPLOAD_FOLDER = Path(
    "uploads/reports"
)

UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp"
}


def allowed_file(filename):

    return (
        "." in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


def report_to_dict(report):

    return {

        "id": report.id,

        "user_id": report.user_id,

        "destination_id": (
            report.destination_id
        ),

        "image_url": (
            report.image_url
        ),

        "user_notes": (
            report.user_notes
        ),

        "admin_notes": (
            report.admin_notes
        ),

        "status": (
            report.status
        ),

        "detected_count": (
            report.detected_count
        ),

        "score": (
            float(report.score)
            if report.score is not None
            else 0.0
        ),

        "created_at": (
            report.created_at.isoformat()
            if report.created_at
            else None
        ),

        "updated_at": (
            report.updated_at.isoformat()
            if report.updated_at
            else None
        )
    }



def update_cleanliness_score(
    destination_id
):
    """
    Menghitung ulang cleanliness score
    berdasarkan seluruh report pada destination.

    Report score:
        0.10 = sedikit sampah
        0.30 = ...
        0.50 = ...
        0.70 = ...
        1.00 = sangat banyak

    Semakin besar report.score:
        semakin kotor.

    Cleanliness:
        1 - rata-rata severity

    Contoh:

        report 1 = 0.10
        report 2 = 0.50

        average = (0.10 + 0.50) / 2
                = 0.30

        cleanliness = 1 - 0.30
                    = 0.70
    """


    reports = (
        Report.query
        .filter_by(
            destination_id=destination_id
        )
        .all()
    )



    if not reports:

        cleanliness_score = 0.50


    else:

        total_severity = sum(
            float(report.score or 0)
            for report in reports
        )

        average_severity = (
            total_severity
            / len(reports)
        )

        cleanliness_score = (
            1 - average_severity
        )


        # Pastikan 0 sampai 1
        cleanliness_score = max(
            0.0,
            min(
                1.0,
                cleanliness_score
            )
        )


    destination = (
        Destination.query.get(
            destination_id
        )
    )


    if not destination:

        raise ValueError(
            "Destination not found"
        )


    destination.cleanliness_score = (
        cleanliness_score
    )


    return cleanliness_score


@reports_bp.route(
    "",
    methods=["GET"]
)
def get_reports():

    reports = (
        Report.query
        .order_by(
            Report.created_at.desc()
        )
        .all()
    )

    return jsonify({

        "success": True,

        "data": [
            report_to_dict(report)
            for report in reports
        ]

    }), 200



@reports_bp.route(
    "/trend",
    methods=["GET"]
)
def get_reports_trend():

    period = request.args.get(
        "period",
        "daily"
    ).lower()


    allowed_periods = {
        "daily",
        "weekly",
        "monthly"
    }


    if period not in allowed_periods:

        return jsonify({

            "success": False,

            "message": (
                "Period must be "
                "daily, weekly, or monthly"
            )

        }), 400


    try:

        today = datetime.now().date()

        if period == "daily":

            # Senin minggu ini
            week_start = (
                today
                - timedelta(
                    days=today.weekday()
                )
            )


            # Senin sampai Minggu
            dates = [

                week_start
                + timedelta(days=i)

                for i in range(7)

            ]


            # Minggu berikutnya
            week_end = (
                week_start
                + timedelta(days=7)
            )


            reports = (
                Report.query
                .filter(
                    Report.created_at
                    >= week_start,

                    Report.created_at
                    < week_end
                )
                .all()
            )


            counts = {
                date: 0
                for date in dates
            }


            for report in reports:

                report_date = (
                    report.created_at.date()
                )


                if report_date in counts:

                    counts[
                        report_date
                    ] += 1


            data = [

                {
                    "label": date.strftime(
                        "%a"
                    ),

                    "date": (
                        date.isoformat()
                    ),

                    "count": (
                        counts[date]
                    )
                }

                for date in dates

            ]

        elif period == "weekly":

            first_day = today.replace(
                day=1
            )


            # Hari pertama bulan berikutnya
            if today.month == 12:

                next_month = today.replace(

                    year=(
                        today.year + 1
                    ),

                    month=1,

                    day=1
                )

            else:

                next_month = today.replace(

                    month=(
                        today.month + 1
                    ),

                    day=1
                )


            reports = (
                Report.query
                .filter(
                    Report.created_at
                    >= first_day,

                    Report.created_at
                    < next_month
                )
                .all()
            )


            counts = {

                1: 0,
                2: 0,
                3: 0,
                4: 0

            }


            for report in reports:

                day = (
                    report.created_at.day
                )


                if day <= 7:

                    week = 1

                elif day <= 14:

                    week = 2

                elif day <= 21:

                    week = 3

                else:

                    week = 4


                counts[week] += 1


            data = [

                {
                    "label": f"W{week}",

                    "week": week,

                    "count": (
                        counts[week]
                    )
                }

                for week in range(1, 5)

            ]


        else:

            # 1 Januari tahun ini
            start_date = datetime(

                today.year,

                1,

                1
            )


            # 1 Januari tahun depan
            end_date = datetime(

                today.year + 1,

                1,

                1
            )


            reports = (
                Report.query
                .filter(
                    Report.created_at
                    >= start_date,

                    Report.created_at
                    < end_date
                )
                .all()
            )


            counts = {

                month: 0

                for month in range(
                    1,
                    13
                )

            }


            for report in reports:

                month = (
                    report.created_at.month
                )

                counts[month] += 1


            data = [

                {
                    "label": datetime(

                        today.year,

                        month,

                        1

                    ).strftime("%b"),

                    "month": month,

                    "count": (
                        counts[month]
                    )
                }

                for month in range(
                    1,
                    13
                )

            ]


        values = [

            item["count"]

            for item in data

        ]


        midpoint = (
            len(values) // 2
        )


        previous_values = (
            values[:midpoint]
        )


        current_values = (
            values[midpoint:]
        )


        previous_total = sum(
            previous_values
        )


        current_total = sum(
            current_values
        )


        if previous_total == 0:

            if current_total > 0:

                percentage = 100

                direction = "up"

            else:

                percentage = 0

                direction = "stable"


        else:

            percentage = round(

                (

                    (
                        current_total
                        - previous_total
                    )

                    / previous_total

                )
                * 100

            )


            if percentage > 0:

                direction = "up"

            elif percentage < 0:

                direction = "down"

            else:

                direction = "stable"


        return jsonify({

            "success": True,

            "period": period,

            "data": data,

            "trend": {

                "percentage": abs(
                    percentage
                ),

                "direction": direction
            }

        }), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "message": (
                "Failed to get "
                "reports trend"
            ),

            "error": str(e)

        }), 500



@reports_bp.route(
    "/<int:report_id>",
    methods=["GET"]
)
def get_report(
    report_id
):

    report = Report.query.get(
        report_id
    )


    if not report:

        return jsonify({

            "success": False,

            "message": (
                "Report not found"
            )

        }), 404


    return jsonify({

        "success": True,

        "data": report_to_dict(
            report
        )

    }), 200


@reports_bp.route(
    "",
    methods=["POST"]
)
def create_report():

    user_id = request.form.get(
        "user_id"
    )

    destination_id = request.form.get(
        "destination_id"
    )

    user_notes = request.form.get(
        "user_notes"
    )


    image = request.files.get(
        "image"
    )



    if not user_id:

        return jsonify({

            "success": False,

            "message": (
                "user_id is required"
            )

        }), 400


    if not destination_id:

        return jsonify({

            "success": False,

            "message": (
                "destination_id is required"
            )

        }), 400


    if not image:

        return jsonify({

            "success": False,

            "message": (
                "Image is required"
            )

        }), 400


    if image.filename == "":

        return jsonify({

            "success": False,

            "message": (
                "Image filename is empty"
            )

        }), 400


    if not allowed_file(
        image.filename
    ):

        return jsonify({

            "success": False,

            "message": (
                "Only JPG, JPEG, PNG, "
                "and WEBP images are allowed"
            )

        }), 400


    user = User.query.get(
        user_id
    )


    if not user:

        return jsonify({

            "success": False,

            "message": (
                "User not found"
            )

        }), 404


    destination = Destination.query.get(
        destination_id
    )


    if not destination:

        return jsonify({

            "success": False,

            "message": (
                "Destination not found"
            )

        }), 404


    original_filename = secure_filename(
        image.filename
    )


    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )


    filename = (
        f"{timestamp}_{original_filename}"
    )


    image_path = (
        UPLOAD_FOLDER / filename
    )


    image.save(
        image_path
    )

    try:



        yolo_result = (
            analyze_photo_for_trash(
                str(image_path)
            )
        )


        detected_count = (
            yolo_result[
                "detected_count"
            ]
        )


        score = (
            yolo_result[
                "score"
            ]
        )


        report = Report(

            user_id=user_id,

            destination_id=destination_id,

            image_url=(
                f"/uploads/reports/"
                f"{filename}"
            ),

            user_notes=user_notes,

            status="pending",

            detected_count=(
                detected_count
            ),

            score=score
        )


        db.session.add(
            report
        )


        db.session.flush()


        cleanliness_score = (
            update_cleanliness_score(
                destination_id
            )
        )


        db.session.commit()


        return jsonify({

            "success": True,

            "message": (
                "Report created successfully"
            ),

            "data": {

                **report_to_dict(
                    report
                ),

                "cleanliness_score": round(
                    cleanliness_score,
                    4
                )
            }

        }), 201


    except Exception as e:


        db.session.rollback()


        if image_path.exists():

            image_path.unlink()


        return jsonify({

            "success": False,

            "message": (
                "Failed to process report"
            ),

            "error": str(e)

        }), 500



@reports_bp.route(
    "/<int:report_id>",
    methods=["PUT"]
)
def update_report(
    report_id
):

    report = Report.query.get(
        report_id
    )


    if not report:

        return jsonify({

            "success": False,

            "message": (
                "Report not found"
            )

        }), 404


    data = (
        request.get_json(
            silent=True
        )
        or {}
    )



    if "user_notes" in data:

        report.user_notes = (
            data["user_notes"]
        )


    if "admin_notes" in data:

        report.admin_notes = (
            data["admin_notes"]
        )


    if "status" in data:

        allowed_status = {

            "pending",

            "resolved"

        }


        if (
            data["status"]
            not in allowed_status
        ):

            return jsonify({

                "success": False,

                "message": (
                    "Invalid status"
                )

            }), 400


        report.status = (
            data["status"]
        )


    try:

        db.session.commit()


        return jsonify({

            "success": True,

            "message": (
                "Report updated successfully"
            ),

            "data": report_to_dict(
                report
            )

        }), 200


    except Exception as e:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message": (
                "Failed to update report"
            ),

            "error": str(e)

        }), 500



@reports_bp.route(
    "/<int:report_id>",
    methods=["DELETE"]
)
def delete_report(
    report_id
):

    report = Report.query.get(
        report_id
    )


    if not report:

        return jsonify({

            "success": False,

            "message": (
                "Report not found"
            )

        }), 404


    # Simpan destination sebelum report dihapus
    destination_id = (
        report.destination_id
    )


    try:



        db.session.delete(
            report
        )


        db.session.flush()


        cleanliness_score = (
            update_cleanliness_score(
                destination_id
            )
        )

        db.session.commit()


        return jsonify({

            "success": True,

            "message": (
                "Report deleted successfully"
            ),

            "data": {

                "cleanliness_score": round(
                    cleanliness_score,
                    4
                )

            }

        }), 200


    except Exception as e:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message": (
                "Failed to delete report"
            ),

            "error": str(e)

        }), 500


@reports_bp.route(
    "/latest",
    methods=["GET"]
)
def get_latest_reports():

    try:

        limit = request.args.get(
            "limit",
            5,
            type=int
        )


        if limit <= 0:

            return jsonify({

                "success": False,

                "message": (
                    "Limit must be greater than 0"
                )

            }), 400


        # Maksimal 5
        limit = min(
            limit,
            5
        )


        reports = (
            Report.query
            .order_by(
                Report.created_at.desc()
            )
            .limit(limit)
            .all()
        )


        return jsonify({

            "success": True,

            "data": [

                report_to_dict(
                    report
                )

                for report in reports

            ]

        }), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "message": (
                "Failed to get latest reports"
            ),

            "error": str(e)

        }), 500