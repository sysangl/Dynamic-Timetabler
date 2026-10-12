from flask import Flask, jsonify, request, render_template, abort
from models import (
    db
)

# helper func
def is_ajax():
    """
    Returns true if the request looks like a JS navigation request
    """

    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def create_routes(app: Flask):

    @app.route("/app/")
    @app.route("/app/<string:page>")
    def serve(page: str = "timetable"):
        """
        Serves a erither a full page or a fragment (AJAX)
        """
        if page not in {"timetable", "settings"}:
            abort(404)

        if is_ajax():
            return page_fragment(page)
        else:
            return render_template("base.html", page=page)

    @app.route("/page/<string:page>", methods=['GET'])
    def page_fragment(page):
        """
        returns page fragment
        """
        template_name = f"{page}.html"
        return render_template(template_name)