from flask import Blueprint, current_app
from werkzeug.local import LocalProxy


bp = Blueprint('gallery', __name__, url_prefix='/gallery')
cache = LocalProxy(lambda: current_app.extensions['cache'].cache)
db = LocalProxy(lambda: current_app.extensions['sqlalchemy'].db)
mongo = LocalProxy(lambda: current_app.extensions['mongoset'])

import models, api, views
