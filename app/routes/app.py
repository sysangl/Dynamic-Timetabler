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
    return redirect(url_for('app.serve',page='timetable'))

@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("base.html", page="timetable")

@bp.route("/<string:page>")
@login_required
def serve(page: str = "timetable"):
    """
    Serves a erither a full page or a fragment (AJAX)
    """
    if page == "dashboard":
        page = "timetable"
    if page not in {"timetable", "settings", "management"}:
        abort(404)

    if is_ajax():
        return page_fragment(page)
    else:
        return render_template("base.html", page=page)

@bp.route("/page/<string:page>", methods=['GET'])
@login_required
def page_fragment(page):
    """
    returns page fragment
    """
    template_name = f"{page}.html"
    return render_template(template_name)