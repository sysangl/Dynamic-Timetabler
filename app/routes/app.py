from flask import Flask, jsonify, request, render_template, abort,redirect, Blueprint,url_for
from flask_login import current_user, login_required
from app.models import (
    db
)

bp = Blueprint('app', __name__)

# helper func
def is_ajax():
    """
    Returns true if the request looks like a JS navigation request
    """

    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

@bp.route("/")
def redirect_to_timetable():
    return redirect(url_for('app.serve_timetable'))

@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("base.html", page="timetable", display_name=current_user.display_name, view=current_user.timetable_view)

@bp.route("/timetable")
@login_required
def serve_timetable():
    if is_ajax():
        return page_fragment('timetable')
    else:
        return render_template("base.html", page='timetable', display_name=current_user.display_name, view=current_user.timetable_view)

@bp.route("/management")
@login_required
def serve_management():
    if is_ajax():
        return page_fragment('management')
    else:
        return render_template("base.html", page='management', display_name=current_user.display_name)

@bp.route("/settings")
@login_required
def serve_settings():
    if is_ajax():
        return page_fragment('settings')
    else:
        return render_template("base.html", page='settings', display_name=current_user.display_name)




@bp.route("/page/<string:page>", methods=['GET'])
@login_required
def page_fragment(page):
    """
    returns page fragment
    """
    template_name = f"{page}.html"
    return render_template(template_name)