set FLASK_APP=src.app
flask db init
flask db migrate -m ""
flask db upgrade