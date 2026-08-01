from functools import lru_cache


@lru_cache(maxsize=1)
def get_face_app():
    """Load the expensive face model only when identity work is requested."""
    from insightface.app import FaceAnalysis

    app = FaceAnalysis(name="buffalo_l")
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app
