import logging
from typing import Any

from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from helpers.datetime import parse_iso_date
from helpers.server import _json_error

bp = Blueprint('app', __name__)

log = logging.getLogger('app')

ALLOWED_PAGES = [
    'timetable',
    'management',
    'settings'
]

# helper func
def _is_ajax():
    """
    Returns true if the request looks like a JS navigation request
    """
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _render(page_name:str, **jinja_vars: Any):
    
    if _is_ajax():
        template = f'{page_name}.html'
        return render_template(template, **jinja_vars),200
    else:
        return render_template("base.html", page=page_name, **jinja_vars), 200

@bp.route("/")
def redirect_to_timetable():
    return redirect(url_for('app.serve_timetable')),302

@bp.route("/dashboard")
@login_required
def dashboard():
    return _render("timetable", display_name=current_user.display_name, view=current_user.settings.timetable_view)

@bp.route("/timetable")
@login_required
def serve_timetable():
    return _render('timetable', display_name=current_user.display_name, view=current_user.settings.timetable_view)

@bp.route("/timetable/<string:date>")
@login_required
def serve_timetable_dated(date):
    parsed_date = parse_iso_date(date)
    if parsed_date:
        return render_template('timetable', display_name=current_user.display_name, display_date = parsed_date, view=current_user.settings.timetable_view)
    else:
        return _json_error(f'"{date}" is not a valid date.', 400)

@bp.route("/management")
@login_required
def serve_management():
    return _render('management', display_name=current_user.display_name)

@bp.route("/settings")
@login_required
def serve_settings():
    return _render('settings', display_name=current_user.display_name)

@bp.route("/page/<string:page>", methods=['GET'])
@login_required
def page_fragment(page, **kwargs):
    """
    returns page fragment
    """
    if page not in ALLOWED_PAGES:
        from flask import abort
        abort(404)
    
    return _render(page, **kwargs)