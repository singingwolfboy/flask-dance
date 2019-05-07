import os
import pytest
import flask
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.consumer.storage import MemoryStorage


betamax = pytest.importorskip("betamax")
GITHUB_ACCESS_TOKEN = os.environ.get("GITHUB_OAUTH_ACCESS_TOKEN", "fake-token")
current_dir = os.path.dirname(__file__)


with betamax.Betamax.configure() as config:
    config.cassette_library_dir = os.path.join(current_dir, "cassettes")
    config.define_cassette_placeholder("<AUTH_TOKEN>", GITHUB_ACCESS_TOKEN)


@pytest.fixture
def app():
    _app = flask.Flask(__name__)
    _app.secret_key = "secret"
    github_bp = make_github_blueprint(
        storage=MemoryStorage({"access_token": GITHUB_ACCESS_TOKEN})
    )
    _app.register_blueprint(github_bp, url_prefix="/login")

    @_app.route("/")
    def index():
        if not github.authorized:
            return redirect(url_for("github.login"))
        resp = github.get("/user")
        assert resp.ok
        return "You are @{login} on GitHub".format(login=resp.json()["login"])

    return _app


@pytest.fixture
def flask_dance_sessions():
    return github


@pytest.mark.usefixtures("betamax_record_flask_dance")
def test_home_page(app):
    with app.test_client() as client:
        response = client.get("/", base_url="https://example.com")
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert text == "You are @singingwolfboy on GitHub"
