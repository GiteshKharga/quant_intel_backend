# app/resources/health.py
from flask.views import MethodView
from flask_smorest import Blueprint

blp = Blueprint("Health", __name__, description="Health check")


@blp.route("/health")
class HealthResource(MethodView):
    def get(self):
        return {"status": "ok"}
