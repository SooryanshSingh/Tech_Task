import onnxruntime as ort
from django.conf import settings
import os
import cv2
import base64
import io

import numpy as np

from PIL import Image

MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "realtime",
    "static",
    "models",
    "yolov8n.onnx"
)
session = ort.InferenceSession(
    MODEL_PATH
)




def decode_base64_image(
    image_b64
):

    if ";base64," in image_b64:

        _, image_b64 = (
            image_b64.split(
                ";base64,"
            )
        )

    image_bytes = (
        base64.b64decode(
            image_b64
        )
    )

    image = Image.open(
        io.BytesIO(
            image_bytes
        )
    ).convert("RGB")

    return np.array(
        image
    )




def preprocess_image(img):

    img = cv2.resize(
        img,
        (640, 640)
    )

    img = img.astype(
        np.float32
    ) / 255.0

    img = np.transpose(
        img,
        (2, 0, 1)
    )

    img = np.expand_dims(
        img,
        axis=0
    )

    return img


def detect_phone_from_output(
    outputs,
    threshold=0.4
):

    predictions = outputs[0][0]

    best_phone_conf = 0

    for i in range(
        predictions.shape[1]
    ):

        detection = predictions[:, i]

        class_scores = detection[4:]

        class_id = int(
            np.argmax(class_scores)
        )

        confidence = float(
            np.max(class_scores)
        )

        if (
            class_id == 67 and
            confidence > best_phone_conf
        ):

            best_phone_conf = confidence

    return (
        best_phone_conf >= threshold,
        best_phone_conf
    )