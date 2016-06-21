from flask import Blueprint
from ..models import Permission

main = Blueprint('main', __name__)

from . import views, errors


# app_context_processor
# let the variable Permission can accessed by all templates
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
