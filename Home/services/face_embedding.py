import cv2
import numpy as np

from .face_model import get_face_app


def extract_embedding(image):

    if isinstance(image, str):

        img = cv2.imread(image)

    else:

        file_bytes = np.frombuffer(
            image.read(),
            np.uint8
        )

        img = cv2.imdecode(
            file_bytes,
            cv2.IMREAD_COLOR
        )

        image.seek(0)

    if img is None:
        return None

    faces = get_face_app().get(img)

    if len(faces) != 1:
        return None

    return faces[0].embedding
