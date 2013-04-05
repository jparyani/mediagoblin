from mediagoblin.tests import tools

import pytest

@pytest.fixture()
def test_app(request):
    """
    py.test fixture to pass sandboxed mediagoblin applications into tests that
    want them.

    You could make a local version of this method for your own tests
    to override the paste and config files being used by passing them
    in differently to get_app.
    """
    return tools.get_app(request)
