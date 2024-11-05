rm -r allocator/migrations
rm db.sqlite3
mkdir allocator/migrations
touch allocator/migrations/__init__.py
python3 manage.py makemigrations
python3 manage.py migrate
python3 builder.py