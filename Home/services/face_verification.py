import cv2
import numpy as np

from .face_model import app


def verify_face(
    stored_embedding,
    image_path
):

    img = cv2.imread(image_path)

    faces = app.get(img)

    if len(faces) == 0:
        return False

    current_embedding = faces[0].embedding

    similarity = np.dot(
        stored_embedding,
        current_embedding
    ) / (
        np.linalg.norm(stored_embedding)
        *
        np.linalg.norm(current_embedding)
    )

    return similarity > 0.75
