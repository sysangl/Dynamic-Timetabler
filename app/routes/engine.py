import logging
from datetime import datetime
from typing import Any

from flask import Blueprint, request
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from helpers.config import get_config
from helpers.datetime import combine_date_time, parse_iso_date
from helpers.server import _json_error, _json_success

from ..extensions import db
from ..models import Activity, Block
from ..engine import initial_table

bp = Blueprint('engine', __name__)

log = logging.getLogger('app')

@bp.route('/generate/<int:id>', methods=['POST'])
@login_required
def generate_activity_group(id):

    activities = Activity.query.filter(
        Activity.owner == current_user,
        Activity.group_id == id
    ).all()

    result = [b.serialise() for b in initial_table(activities, current_user)]

    log.info(result)

    return _json_success({'blocks':result})