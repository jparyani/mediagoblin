from routes import Mapper

mapping = Mapper()
mapping.minimization = False

mapping.connect(
    "index", "/", controller="mediagoblin.views:root_view")
