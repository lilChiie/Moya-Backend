import os
from ultralytics import YOLO
import cv2


MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "models",
    "yolo",
    "best.pt"
)

try:
    model = YOLO(MODEL_PATH)
except Exception as e:
    print(f"Error loading YOLO model from {MODEL_PATH}: {e}")
    model = None


def get_severity_score(trash_count):
    if trash_count <= 3:
        return 0.10
    elif trash_count <= 6:
        return 0.30
    elif trash_count <= 9:
        return 0.50
    elif trash_count <= 12:
        return 0.70
    else:
        return 1.00


def analyze_photo_for_trash(photo_path):
    """
    Analyzes a photo for trash using YOLO11s.

    Returns:
        detected_count: jumlah sampah yang terdeteksi
        score: severity score berdasarkan jumlah sampah
    """

    if model is None:
        print("YOLO model not loaded.")

        return {
            "detected_count": 0,
            "score": 0.10
        }

    try:

        results = list(model(photo_path))
        result = results[0]

        trash_count = len(result.boxes)

        severity_score = get_severity_score(trash_count)

        annotated_img = result.plot()

        cv2.imwrite(photo_path, annotated_img)

        print(f"Trash detected : {trash_count}")
        print(f"Severity score : {severity_score}")

        return {
            "detected_count": trash_count,
            "score": severity_score
        }

    except Exception as e:
        print(f"Error during YOLO inference: {e}")

        return {
            "detected_count": 0,
            "score": 0.10
        }