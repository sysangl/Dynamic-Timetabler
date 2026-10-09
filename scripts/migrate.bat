set FLASK_APP=FLASK_APP
flask db init
flask db migrate -m "initial tables"
flask db upgrade