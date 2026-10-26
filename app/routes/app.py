from flask import jsonify, request, render_template, abort,redirect, Blueprint,url_for
from flask_login import current_user, login_required
from helpers.datetime import parse_iso_date

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
    return render_template("base.html", page="timetable", display_name=current_user.display_name)

@bp.route("/timetable")
@login_required
def serve_timetable():
    if is_ajax():
        return page_fragment('timetable',view=current_user.settings.timetable_view)
    else:
        return render_template("base.html", page='timetable', display_name=current_user.display_name)

@bp.route("/timetable/<string:date>")
@login_required
def serve_timetable_dated(date):
    parsed_date = parse_iso_date(date)
    if parsed_date:
        if is_ajax():
            return page_fragment('timetable',view=current_user.settings.timetable_view, display_date = parsed_date)
        else:
            return render_template("base.html", page='timetable', display_name=current_user.display_name, display_date = parsed_date)
    else:
        return jsonify({'error':f'"{date}" is not a valid date.'}), 400

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
def page_fragment(page, **kwargs):
    """
    returns page fragment
    """
    template_name = f"{page}.html"
    return render_template(template_name, **kwargs)