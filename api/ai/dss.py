from math import radians, sin, cos, sqrt, atan2

from api.models import (
    Destination,
    Report
)
from models.destination import destination_tourisms, destination_accessibilities
from api.extensions import db


WEIGHTS = {
    "accessibility": 0.20,
    "budget": 0.25,
    "duration": 0.20,
    "distance": 0.25,
    "cleanliness": 0.10
}


def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Menghitung jarak antara dua koordinat
    menggunakan Haversine Formula.
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

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c


def calculate_accessibility_score(
    destination_id,
    accessibility_ids
):
    """
    Menghitung kecocokan accessibility.

    Contoh:

    User memilih:
        [1, 2, 3]

    Destination memiliki:
        [1, 2]

    Maka:
        2 / 3 = 0.67

    Semakin banyak accessibility yang cocok,
    semakin tinggi score.
    """

    if not accessibility_ids:
        return 0.0

    destination_accessibilities_data = (
        db.session.query(destination_accessibilities)
        .filter(
            destination_accessibilities.c.destination_id
            == destination_id,

            destination_accessibilities.c.accessibility_id.in_(
                accessibility_ids
            )
        )
        .all()
    )

    matched_count = len(
        destination_accessibilities_data
    )

    total_requested = len(
        accessibility_ids
    )

    return matched_count / total_requested


def get_cleanliness_score(destination_id):
    """
    Mengambil seluruh report pada destination.

    Report score:
        tingkat keparahan sampah.

    Semakin besar severity:
        semakin kotor.

    Cleanliness:
        1 - rata-rata severity.

    Jika belum ada report:
        cleanliness = 0.5
    """

    reports = (
        Report.query
        .filter_by(
            destination_id=destination_id
        )
        .all()
    )

    if not reports:
        return 0.5

    total_severity = sum(
        float(report.score)
        for report in reports
    )

    average_severity = (
        total_severity
        / len(reports)
    )

    cleanliness = (
        1 - average_severity
    )

    return max(
        0.0,
        min(1.0, cleanliness)
    )


def calculate_budget_score(
    entrance_fee,
    budget
):
    """
    Budget merupakan kriteria COST.

    Semakin murah dibanding budget,
    semakin tinggi nilainya.

    Jika harga melebihi budget:
        score = 0
    """

    entrance_fee = float(
        entrance_fee or 0
    )

    budget = float(
        budget or 0
    )

    if budget <= 0:
        return 0.0

    if entrance_fee > budget:
        return 0.0

    return 1 - (
        entrance_fee / budget
    )


def calculate_duration_score(
    destination_duration,
    available_duration
):
    """
    Mengukur kecocokan durasi destinasi
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

    return (
        destination_duration
        / available_duration
    )



def calculate_distance_score(
    distance,
    max_distance
):
    """
    Jarak merupakan kriteria COST.

    Semakin dekat:
        semakin tinggi score.
    """

    distance = float(distance)
    max_distance = float(max_distance)

    if max_distance <= 0:
        return 0.0

    if distance > max_distance:
        return 0.0

    return 1 - (
        distance / max_distance
    )


def run_dss(
    accessibility_ids,
    tourism_id,
    budget,
    duration_minutes,
    max_distance_km,
    user_latitude=None,
    user_longitude=None
):
    """
    Menjalankan DSS menggunakan metode SAW.

    Input:
        accessibility_ids = list accessibility yang dipilih user
        tourism_id        = satu kategori wisata
        budget            = budget user
        duration_minutes  = durasi perjalanan user
        max_distance_km   = jarak maksimal
        user_latitude     = latitude user
        user_longitude    = longitude user

    Criteria:

        Accessibility = 20%
        Budget        = 25%
        Duration      = 20%
        Distance      = 25%
        Cleanliness   = 10%

    Hasil:
        TOP 5 destinasi dengan score tertinggi.
    """


    if accessibility_ids is None:
        accessibility_ids = []


    accessibility_ids = list(
        set(
            int(accessibility_id)
            for accessibility_id
            in accessibility_ids
        )
    )


    destination_tourisms_data = (
        db.session.query(destination_tourisms)
        .filter(
            destination_tourisms.c.tourism_id == tourism_id
        )
        .all()
    )

    destination_ids = [
        item.destination_id
        for item in destination_tourisms_data
    ]

    if not destination_ids:
        return []

    destinations = (
        Destination.query
        .filter(
            Destination.id.in_(
                destination_ids
            )
        )
        .all()
    )

    results = []


    for destination in destinations:


        accessibility_score = (
            calculate_accessibility_score(
                destination.id,
                accessibility_ids
            )
        )

        budget_score = (
            calculate_budget_score(
                destination.entrance_fee,
                budget
            )
        )

        entrance_fee = float(
            destination.entrance_fee or 0
        )


        if entrance_fee > float(budget):
            continue


        duration_score = (
            calculate_duration_score(
                destination.estimated_duration,
                duration_minutes
            )
        )

        if (
            float(
                destination.estimated_duration or 0
            )
            > float(duration_minutes)
        ):
            continue


        if (
            user_latitude is not None
            and user_longitude is not None
        ):

            if (
                destination.latitude is None
                or destination.longitude is None
            ):
                continue

            distance = calculate_distance_km(
                user_latitude,
                user_longitude,
                destination.latitude,
                destination.longitude
            )

    
            if distance > float(
                max_distance_km
            ):
                continue

            distance_score = (
                calculate_distance_score(
                    distance,
                    max_distance_km
                )
            )

        else:

            distance = None
            distance_score = 0.5

        cleanliness_score = (
            get_cleanliness_score(
                destination.id
            )
        )


        final_score = (

            accessibility_score
            * WEIGHTS["accessibility"]

            +

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

            "destination_id":
                destination.id,

            "destination_name":
                destination.name,

            "accessibility_score":
                round(
                    accessibility_score,
                    4
                ),

            "budget_score":
                round(
                    budget_score,
                    4
                ),

            "duration_score":
                round(
                    duration_score,
                    4
                ),

            "distance_score":
                round(
                    distance_score,
                    4
                ),

            "cleanliness_score":
                round(
                    cleanliness_score,
                    4
                ),

            "distance_km": (
                round(distance, 2)
                if distance is not None
                else None
            ),

            "final_score":
                round(
                    final_score,
                    4
                )
        })


    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    results = results[:5]

    for index, result in enumerate(
        results,
        start=1
    ):
        result["rank"] = index

    return results