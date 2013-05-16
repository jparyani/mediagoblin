from mediagoblin.tools import staticdirect
from mediagoblin.tools.testing import _activate_testing

_activate_testing()


def test_staticdirect():
    sdirect = staticdirect.StaticDirect(
      {None: "/static/",
       "theme": "http://example.org/themestatic"})
    assert sdirect("css/monkeys.css") == "/static/css/monkeys.css"
    assert sdirect("images/lollerskate.png", "theme") == \
        "http://example.org/themestatic/images/lollerskate.png"
