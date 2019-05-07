import pytest
import responses as resp_module


@pytest.fixture
def responses(request):
    """
    Set up the `responses` module for mocking HTTP requests

    https://github.com/getsentry/responses
    """
    resp_module.start()

    def done():
        resp_module.stop()
        resp_module.reset()

    request.addfinalizer(done)
