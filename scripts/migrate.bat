set FLASK_APP=src.app
flask db migrate -m ""
flask db upgrade