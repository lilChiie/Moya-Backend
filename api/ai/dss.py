from math import radians, sin, cos, sqrt, atan2

from api.models import (
    db,
    Destination,
    Report
)


WEIGHTS = {
    "budget": 0.30,
    "duration": 0.25,
    "distance": 0.35,
    "cleanliness": 0.10
}


def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Menghitung jarak antara dua koordinat menggunakan
    Haversine Formula.
    """

    R = 6371.0

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c



def get_cleanliness_score(destination_id):
    """
    Mengambil seluruh report pada destination.

    Report score = tingkat keparahan sampah.
    Semakin besar score -> semakin kotor.

    Cleanliness:
        1 - rata-rata severity
    """

    reports = (
        Report.query
        .filter_by(destination_id=destination_id)
        .all()
    )

    # Belum ada report
    if not reports:
        return 0.5

    total_severity = sum(
        float(report.score)
        for report in reports
    )

    average_severity = (
        total_severity / len(reports)
    )

    cleanliness = 1 - average_severity

    # Pastikan 0 sampai 1
    return max(0.0, min(1.0, cleanliness))


def calculate_budget_score(
    entrance_fee,
    budget
):
    """
    Budget merupakan kriteria COST.

    Semakin murah dibanding budget,
    semakin tinggi nilainya.

    Jika harga melebihi budget -> 0.
    """

    entrance_fee = float(entrance_fee or 0)
    budget = float(budget or 0)

    if budget <= 0:
        return 0.0

    if entrance_fee > budget:
        return 0.0

    return 1 - (entrance_fee / budget)


def calculate_duration_score(
    destination_duration,
    available_duration
):
    """
    Mengukur seberapa cocok durasi destinasi
    dengan durasi perjalanan user.
    """

    destination_duration = float(
        destination_duration or 0
    )

    available_duration = float(
        available_duration or 0
    )

    if available_duration <= 0:
        return 0.0

    if destination_duration > available_duration:
        return 0.0

    return destination_duration / available_duration


def calculate_distance_score(
    distance,
    max_distance
):
    """
    Jarak merupakan kriteria COST.

    Semakin dekat -> semakin tinggi score.
    """

    distance = float(distance)
    max_distance = float(max_distance)

    if max_distance <= 0:
        return 0.0

    if distance > max_distance:
        return 0.0

    return 1 - (distance / max_distance)


def run_dss(
    accessibility_id,
    tourism_id,
    budget,
    duration_minutes,
    max_distance_km,
    user_latitude=None,
    user_longitude=None
):
    """
    Menjalankan DSS menggunakan metode SAW.

    Accessibility dan tourism digunakan sebagai FILTER.

    SAW criteria:
        Budget      = 30%
        Duration    = 25%
        Distance    = 35%
        Cleanliness = 10%
    """


    destinations = (
        Destination.query
        .filter(
            Destination.accessibility_id == accessibility_id,
            Destination.tourism_id == tourism_id
        )
        .all()
    )

    results = []

    for destination in destinations:


        budget_score = calculate_budget_score(
            destination.entrance_fee,
            budget
        )

        if budget_score == 0:
            continue

        duration_score = calculate_duration_score(
            destination.estimated_duration,
            duration_minutes
        )

        if duration_score == 0:
            continue

        if (
            user_latitude is not None
            and user_longitude is not None
        ):

            distance = calculate_distance_km(
                user_latitude,
                user_longitude,
                destination.latitude,
                destination.longitude
            )

            if distance > max_distance_km:
                continue

            distance_score = calculate_distance_score(
                distance,
                max_distance_km
            )

        else:
        
            distance = None
            distance_score = 0.5


        cleanliness_score = get_cleanliness_score(
            destination.id
        )

        final_score = (
            budget_score
            * WEIGHTS["budget"]
            +
            duration_score
            * WEIGHTS["duration"]
            +
            distance_score
            * WEIGHTS["distance"]
            +
            cleanliness_score
            * WEIGHTS["cleanliness"]
        )

        results.append({
            "destination_id": destination.id,
            "destination_name": destination.name,

            "budget_score": round(
                budget_score, 4
            ),

            "duration_score": round(
                duration_score, 4
            ),

            "distance_score": round(
                distance_score, 4
            ),

            "cleanliness_score": round(
                cleanliness_score, 4
            ),

            "distance_km": (
                round(distance, 2)
                if distance is not None
                else None
            ),

            "final_score": round(
                final_score, 4
            )
        })


    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    for index, result in enumerate(
        results,
        start=1
    ):
        result["rank"] = index

    return results