rm -r instance
rm -r migrations
flask db init
flask db migrate -m "Fresh migration"
flask db upgrade