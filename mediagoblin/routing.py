from routes import Mapper

def get_mapper():
    mapping = Mapper()
    mapping.minimization = False

    mapping.connect(
        "index", "/",
        controller="mediagoblin.views:root_view")
    mapping.connect(
        "test_submit", "/test_submit/",
        controller="mediagoblin.views:submit_test")

    return mapping
