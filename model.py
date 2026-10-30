from flask_sqlalchemy import SQLAlchemy

# db is created with no app attached, so model.py can be imported anywhere.
# app.py will connect it to Flask later with db.init_app(app).
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)   # will store a hash, not plain text
    role = db.Column(db.String(20), nullable=False)        # admin / examiner / student
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    roll_no = db.Column(db.String(30))
    status = db.Column(db.String(20), nullable=False, default="active")

class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    credits = db.Column(db.Integer, default=3)
    status = db.Column(db.String(20), nullable=False, default="Active")  # Active / Inactive