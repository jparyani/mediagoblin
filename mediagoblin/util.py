import jinja2

def get_jinja_env(user_template_path=None):
    if user_template_path:
        loader = jinja2.ChoiceLoader(
            [jinja2.FileSystemLoader(user_template_path),
             jinja2.PackageLoader('mediagoblin', 'templates')])
    else:
        loader = jinja2.PackageLoader('mediagoblin', 'templates')

    return jinja2.Environment(loader=loader, autoescape=True)
