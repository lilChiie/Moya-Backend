from flask import Blueprint, jsonify

from api.models import Destination, Report


spot_bp = Blueprint(
    "spots",
    __name__
)


# ============================================================
# GET ALL SPOTS
# ============================================================

@spot_bp.route("/", methods=["GET"])
def get_spots():

    try:

        destinations = (
            Destination.query
            .order_by(
                Destination.id.asc()
            )
            .all()
        )

        result = []

        for spot in destinations:

            # ================================================
            # CLEANLINESS SCORE
            # ================================================

            cleanliness_score = (
                float(spot.cleanliness_score)
                if spot.cleanliness_score is not None
                else 0.5
            )


            # ================================================
            # CLEANLINESS STATUS
            # ================================================

            cleanliness_status = (
                spot.cleanliness_status
                if spot.cleanliness_status
                else "Needs Attention"
            )


            # ================================================
            # STATUS UNTUK FE
            # ================================================

            if cleanliness_status == "Safe":

                status = "Aman"

            elif cleanliness_status == "Needs Attention":

                status = "Perlu Perhatian"

            else:

                status = "Perlu Penanganan"


            # ================================================
            # JUMLAH REPORT
            # ================================================

            report_count = (
                Report.query
                .filter_by(
                    destination_id=spot.id
                )
                .count()
            )


            # ================================================
            # IMAGE
            # ================================================

            image_url = getattr(
                spot,
                "image_url",
                None
            )


            # ================================================
            # RESPONSE
            # ================================================

            result.append({

                "id": spot.id,

                "name": spot.name,

                "description": getattr(
                    spot,
                    "description",
                    None
                ),

                "latitude": (
                    float(spot.latitude)
                    if spot.latitude is not None
                    else None
                ),

                "longitude": (
                    float(spot.longitude)
                    if spot.longitude is not None
                    else None
                ),

                # Status Indonesia untuk FE lama
                "status": status,

                # Status asli database
                "cleanliness_status": (
                    cleanliness_status
                ),

                "cleanliness_score": round(
                    cleanliness_score,
                    4
                ),

                "image_url": image_url,

                "created_at": (
                    spot.created_at.isoformat()
                    if getattr(
                        spot,
                        "created_at",
                        None
                    )
                    else None
                ),

                # FE kamu menggunakan ini
                "laporanCount": report_count,

                # FE map
                "coords": [
                    (
                        float(spot.latitude)
                        if spot.latitude is not None
                        else None
                    ),
                    (
                        float(spot.longitude)
                        if spot.longitude is not None
                        else None
                    )
                ],

                # FE kamu menggunakan d.img
                "img": image_url

            })


        return jsonify(result), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "message": (
                "Failed to get spots"
            ),

            "error": str(e)

        }), 500


# ============================================================
# GET SINGLE SPOT
# ============================================================

@spot_bp.route(
    "/<int:id>",
    methods=["GET"]
)
def get_spot(id):

    try:

        spot = Destination.query.get(id)


        if not spot:

            return jsonify({

                "success": False,

                "message": "Spot not found"

            }), 404


        # ================================================
        # GET REPORTS
        # ================================================

        reports = (

            Report.query

            .filter_by(
                destination_id=spot.id
            )

            .order_by(
                Report.created_at.desc()
            )

            .all()

        )


        reports_data = []


        for report in reports:

            reports_data.append({

                "id": report.id,

                "image_url": (
                    report.image_url
                ),

                "detected_count": (
                    report.detected_count
                ),

                "score": (
                    float(report.score)
                    if report.score is not None
                    else 0.0
                ),

                "status": (
                    report.status
                ),

                "admin_notes": (
                    report.admin_notes
                ),

                "user_notes": (
                    report.user_notes
                ),

                "created_at": (

                    report.created_at.isoformat()

                    if report.created_at

                    else None

                )

            })


        # ================================================
        # CLEANLINESS
        # ================================================

        cleanliness_score = (

            float(spot.cleanliness_score)

            if spot.cleanliness_score is not None

            else 0.5

        )


        cleanliness_status = (

            spot.cleanliness_status

            if spot.cleanliness_status

            else "Needs Attention"

        )


        if cleanliness_status == "Safe":

            status = "Aman"

        elif cleanliness_status == "Needs Attention":

            status = "Perlu Perhatian"

        else:

            status = "Perlu Penanganan"


        # ================================================
        # IMAGE
        # ================================================

        image_url = getattr(
            spot,
            "image_url",
            None
        )


        # ================================================
        # RESPONSE
        # ================================================

        result = {

            "id": spot.id,

            "name": spot.name,

            "description": getattr(
                spot,
                "description",
                None
            ),

            "latitude": (

                float(spot.latitude)

                if spot.latitude is not None

                else None

            ),

            "longitude": (

                float(spot.longitude)

                if spot.longitude is not None

                else None

            ),

            "status": status,

            "cleanliness_status": (
                cleanliness_status
            ),

            "cleanliness_score": round(
                cleanliness_score,
                4
            ),

            "image_url": image_url,

            "created_at": (

                spot.created_at.isoformat()

                if getattr(
                    spot,
                    "created_at",
                    None
                )

                else None

            ),

            "laporanCount": len(
                reports
            ),

            "coords": [

                (
                    float(spot.latitude)

                    if spot.latitude is not None

                    else None

                ),

                (
                    float(spot.longitude)

                    if spot.longitude is not None

                    else None

                )

            ],

            "img": image_url,

            "reports": reports_data

        }


        return jsonify(result), 200


    except Exception as e:

        return jsonify({

            "success": False,

            "message": (
                "Failed to get spot"
            ),

            "error": str(e)

        }), 500