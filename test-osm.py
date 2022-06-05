from flask import Flask, redirect, url_for
from flask_dance.contrib.osm import make_osm_blueprint, osm

app = Flask(__name__)
app.secret_key = "kskijowsdenfolwnlfknw"  # Replace this with your own secret!
blueprint = make_osm_blueprint(
    client_id="QqOjU6MRsjtRMVEQ38XPlIUm3CVjBLEE5xezFUvi0YM",
    client_secret="5OrHFE570MrShxyTlsbXAv9kl4WOXY26Zt_M9vOtzVc",
    redirect_url="http://localhost:5000/login/osm/authorized",
)
app.register_blueprint(blueprint, url_prefix="/login")


@app.route("/")
def index():
    if not osm.authorized:
        return redirect(url_for("osm.login"))
    resp = osm.get("/user")
    assert resp.ok
    return "You are @{login} on OSM".format(login=resp.json()["login"])
