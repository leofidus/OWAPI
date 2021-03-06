"""
Main OWAPI App.
"""
import json
import logging
import traceback

from asphalt.core import ContainerComponent
from asphalt.redis.component import RedisComponent
from kyoukai import Blueprint
from kyoukai import HTTPException
from kyoukai import Kyoukai
from kyoukai.asphalt import KyoukaiComponent
from kyoukai.context import HTTPRequestContext
from kyoukai.response import Response

from owapi.v2 import routes

# Fuck your logging config.
from owapi.v2.routes import api_v2
from owapi.v3 import api_v3

logging.basicConfig(filename='/dev/null', level=logging.INFO)

formatter = logging.Formatter('%(asctime)s - [%(levelname)s] %(name)s -> %(message)s')
root = logging.getLogger()

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(formatter)
root.addHandler(consoleHandler)

logger = logging.getLogger("OWAPI")

class APIComponent(ContainerComponent):
    """
    Container for other components. I think.
    """

    async def start(self, ctx):
        self.add_component('kyoukai', KyoukaiComponent, ip="127.0.0.1", port=4444,
                           app="app:app", template_renderer=None)
        self.add_component('redis', RedisComponent)
        await super().start(ctx)

        logger.info("Started OWAPI server.")


app = Kyoukai("owapi")


@app.route("/")
async def root(ctx: HTTPRequestContext):
    return Response.redirect("https://github.com/SunDwarf/OWAPI/blob/master/api.md")


@app.root.errorhandler(500)
async def e500(ctx: HTTPRequestContext, exc: HTTPException):
    obb = {
        "error": 500,
        "msg": "please report this!",
        "exc": repr(exc.__cause__)
    }
    logger.error("Unhandled exception - Blizzard format probably changed!")
    traceback.print_exc()
    return json.dumps(obb), 500, {"Content-Type": "application/json"}


@app.root.errorhandler(404)
async def e404(ctx: HTTPRequestContext, exc: HTTPException):
    return json.dumps({"error": 404}), 404, {"Content-Type": "application/json"}


# Create the api blueprint and add children
api_bp = Blueprint("api", url_prefix="/api")


@api_bp.after_request
async def jsonify(ctx, response: Response):
    """
    JSONify the response.
    """
    if isinstance(response.body, str):
        return response

    # json.dump the body.
    status_code = response.code
    if not any(response.body.values()):
        status_code = 404
    d = json.dumps(response.body)
    response.body = d
    response.headers["Content-Type"] = "application/json"
    response.code = status_code
    return response


api_bp.add_child(api_v2)
api_bp.add_child(api_v3)

app.register_blueprint(api_bp)
