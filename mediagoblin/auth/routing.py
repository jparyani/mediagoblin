from routes.route import Route

auth_routes = [
    Route('mediagoblin.auth.register', '/register/',
          controller='mediagoblin.auth.views:register'),
    Route('mediagoblin.auth.register_success', '/register/success/',
          controller='mediagoblin.auth.views:register_success'),
    Route('mediagoblin.auth.login', '/login/',
          controller='mediagoblin.auth.views:login'),
    Route('mediagoblin.auth.logout', '/logout/',
          controller='mediagoblin.auth.views:logout')]
