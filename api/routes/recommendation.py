from flask import Blueprint, request, jsonify

from api.models import (
    db,
    RecomRequest,
    RecomResult,
    Itinerary,
    ItineraryItem,
    User,
    Accessibility,
    Tourism,
    Destination
)

from api.ai.dss import run_dss


recommendation_bp = Blueprint(
    "recommendation",
    __name__,
    url_prefix="/api/recommendation"
)


def recommendation_to_dict(result):
    return {
        "id": result.id,
        "request_id": result.request_id,
        "destination_id": result.destination_id,
        "reason": result.reason,
        "created_at": (
            result.created_at.isoformat()
            if result.created_at
            else None
        )
    }


def itinerary_item_to_dict(item):
    destination = item.destination

    return {
        "id": item.id,
        "destination_id": item.destination_id,
        "destination_name": (
            destination.name
            if destination
            else None
        ),
        "sequence": item.sequence,
        "start_time": (
            item.start_time.isoformat()
            if item.start_time
            else None
        ),
        "duration_minutes": item.duration_minutes
    }


@recommendation_bp.route("", methods=["POST"])
def create_recommendation():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body must be JSON"
        }), 400


    user_id = data.get("user_id")
    accessibility_id = data.get("accessibility_id")
    tourism_id = data.get("tourism_id")
    budget = data.get("budget")
    duration_minutes = data.get("duration_minutes")
    max_distance_km = data.get("max_distance_km")

    latitude = data.get("latitude")
    longitude = data.get("longitude")


    required_fields = {
        "user_id": user_id,
        "accessibility_id": accessibility_id,
        "tourism_id": tourism_id,
        "budget": budget,
        "duration_minutes": duration_minutes,
        "max_distance_km": max_distance_km
    }

    missing_fields = [
        field
        for field, value in required_fields.items()
        if value is None
    ]

    if missing_fields:
        return jsonify({
            "success": False,
            "message": "Missing required fields",
            "fields": missing_fields
        }), 400


    try:
        user_id = int(user_id)
        accessibility_id = int(accessibility_id)
        tourism_id = int(tourism_id)

        budget = float(budget)
        duration_minutes = int(duration_minutes)
        max_distance_km = float(max_distance_km)

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "Invalid input format"
        }), 400

    if budget < 0:
        return jsonify({
            "success": False,
            "message": "Budget cannot be negative"
        }), 400

    if duration_minutes <= 0:
        return jsonify({
            "success": False,
            "message": "duration_minutes must be greater than 0"
        }), 400

    if max_distance_km <= 0:
        return jsonify({
            "success": False,
            "message": "max_distance_km must be greater than 0"
        }), 400


    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404


    accessibility = Accessibility.query.get(
        accessibility_id
    )

    if not accessibility:
        return jsonify({
            "success": False,
            "message": "Accessibility not found"
        }), 404


    tourism = Tourism.query.get(tourism_id)

    if not tourism:
        return jsonify({
            "success": False,
            "message": "Tourism category not found"
        }), 404


    if latitude is not None or longitude is not None:

        if latitude is None or longitude is None:
            return jsonify({
                "success": False,
                "message": "latitude and longitude must be provided together"
            }), 400

        try:
            latitude = float(latitude)
            longitude = float(longitude)

        except (ValueError, TypeError):

            return jsonify({
                "success": False,
                "message": "Invalid latitude or longitude"
            }), 400


    recom_request = RecomRequest(
        user_id=user_id,
        accessibility_id=accessibility_id,
        tourism_id=tourism_id,
        budget=budget,
        duration_minutes=duration_minutes,
        max_distance_km=max_distance_km
    )

    db.session.add(recom_request)

    try:
        db.session.flush()

        dss_results = run_dss(
            accessibility_id=accessibility_id,
            tourism_id=tourism_id,
            budget=budget,
            duration_minutes=duration_minutes,
            max_distance_km=max_distance_km,
            user_latitude=latitude,
            user_longitude=longitude
        )


        if not dss_results:

            db.session.rollback()

            return jsonify({
                "success": False,
                "message": (
                    "No destinations match your "
                    "requirements"
                )
            }), 404

        saved_results = []

        for result in dss_results:

            destination_id = result["destination_id"]
            final_score = result["final_score"]

            reason = (
                f"Recommendation score: {final_score:.2f}. "
                f"Budget score: {result['budget_score']:.2f}, "
                f"duration score: {result['duration_score']:.2f}, "
                f"distance score: {result['distance_score']:.2f}, "
                f"cleanliness score: "
                f"{result['cleanliness_score']:.2f}."
            )

            recom_result = RecomResult(
                request_id=recom_request.id,
                destination_id=destination_id,
                reason=reason
            )

            db.session.add(recom_result)

            saved_results.append({
                "recom_result": recom_result,
                "dss_result": result
            })

        db.session.flush()


        itinerary = Itinerary(
            user_id=user_id,
            recom_request_id=recom_request.id,
            name=f"{tourism.name} Recommendation",
            route_type="DSS",
            total_duration=0,
            total_cost=0,
            detected_count=0
        )

        db.session.add(itinerary)
        db.session.flush()


        total_duration = 0
        total_cost = 0
        sequence = 1

        for item in saved_results:

            dss_result = item["dss_result"]

            destination = Destination.query.get(
                dss_result["destination_id"]
            )

            if not destination:
                continue

            destination_duration = (
                destination.estimated_duration or 0
            )

            destination_cost = (
                float(destination.entrance_fee or 0)
            )


            if (
                total_duration
                + destination_duration
                > duration_minutes
            ):
                continue


            if (
                total_cost
                + destination_cost
                > budget
            ):
                continue

            itinerary_item = ItineraryItem(
                itinerary_id=itinerary.id,
                destination_id=destination.id,
                sequence=sequence,
                start_time=None,
                duration_minutes=destination_duration
            )

            db.session.add(itinerary_item)

            total_duration += destination_duration
            total_cost += destination_cost

            sequence += 1



        itinerary.total_duration = total_duration
        itinerary.total_cost = total_cost

        db.session.commit()



        itinerary_items = (
            ItineraryItem.query
            .filter_by(
                itinerary_id=itinerary.id
            )
            .order_by(
                ItineraryItem.sequence.asc()
            )
            .all()
        )

        recommendations = []

        for item in saved_results:

            result = item["recom_result"]
            dss_result = item["dss_result"]

            recommendations.append({
                "id": result.id,
                "destination_id": result.destination_id,
                "destination_name": (
                    dss_result["destination_name"]
                ),
                "rank": dss_result["rank"],
                "final_score": dss_result["final_score"],
                "budget_score": dss_result["budget_score"],
                "duration_score": dss_result["duration_score"],
                "distance_score": dss_result["distance_score"],
                "cleanliness_score": (
                    dss_result["cleanliness_score"]
                ),
                "distance_km": dss_result["distance_km"],
                "reason": result.reason
            })

        return jsonify({
            "success": True,
            "message": "Recommendation generated successfully",

            "data": {
                "request": {
                    "id": recom_request.id,
                    "user_id": recom_request.user_id,
                    "accessibility_id": (
                        recom_request.accessibility_id
                    ),
                    "tourism_id": recom_request.tourism_id,
                    "budget": float(
                        recom_request.budget
                    ),
                    "duration_minutes": (
                        recom_request.duration_minutes
                    ),
                    "max_distance_km": float(
                        recom_request.max_distance_km
                    )
                },

                "recommendations": recommendations,

                "itinerary": {
                    "id": itinerary.id,
                    "name": itinerary.name,
                    "route_type": itinerary.route_type,
                    "total_duration": (
                        itinerary.total_duration
                    ),
                    "total_cost": float(
                        itinerary.total_cost
                    ),
                    "items": [
                        itinerary_item_to_dict(item)
                        for item in itinerary_items
                    ]
                }
            }
        }), 201

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Failed to generate recommendation",
            "error": str(e)
        }), 500



@recommendation_bp.route(
    "/<int:request_id>",
    methods=["GET"]
)
def get_recommendation(request_id):


    recom_request = RecomRequest.query.get(request_id)

    if not recom_request:

        return jsonify({
            "success": False,
            "message": "Recommendation request not found"
        }), 404


    results = (
        RecomResult.query
        .filter_by(request_id=request_id)
        .all()
    )

    itinerary = (
        Itinerary.query
        .filter_by(
            recom_request_id=request_id
        )
        .first()
    )

    itinerary_data = None

    if itinerary:

        items = (
            ItineraryItem.query
            .filter_by(
                itinerary_id=itinerary.id
            )
            .order_by(
                ItineraryItem.sequence.asc()
            )
            .all()
        )

        itinerary_data = {
            "id": itinerary.id,
            "name": itinerary.name,
            "route_type": itinerary.route_type,
            "total_duration": itinerary.total_duration,
            "total_cost": float(
                itinerary.total_cost or 0
            ),
            "items": [
                itinerary_item_to_dict(item)
                for item in items
            ]
        }

    return jsonify({
        "success": True,

        "data": {
            "request": {
                "id": recom_request.id,
                "user_id": recom_request.user_id,
                "accessibility_id": (
                    recom_request.accessibility_id
                ),
                "tourism_id": recom_request.tourism_id,
                "budget": float(
                    recom_request.budget or 0
                ),
                "duration_minutes": (
                    recom_request.duration_minutes
                ),
                "max_distance_km": float(
                    recom_request.max_distance_km or 0
                ),
                "created_at": (
                    recom_request.created_at.isoformat()
                    if recom_request.created_at
                    else None
                )
            },

            "recommendations": [
                recommendation_to_dict(result)
                for result in results
            ],

            "itinerary": itinerary_data
        }
    }), 200