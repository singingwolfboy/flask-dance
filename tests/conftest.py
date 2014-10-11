import pytest
import responses as resp_module


@pytest.fixture
def responses(request):
    resp_module.start()
    def done():
        resp_module.stop()
        resp_module.reset()
    request.addfinalizer(done)
