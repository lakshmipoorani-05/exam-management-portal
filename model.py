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

class Exam(db.Model):
    __tablename__ = "exams"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    exam_type = db.Column(db.String(30), nullable=False)   # Viva / Practical / Project Demo / Assessment
    duration = db.Column(db.Integer, nullable=False)       # minutes
    max_marks = db.Column(db.Integer, nullable=False)
    slot_create_start = db.Column(db.Date, nullable=False)
    slot_create_end = db.Column(db.Date, nullable=False)
    booking_start = db.Column(db.Date, nullable=False)
    booking_end = db.Column(db.Date, nullable=False)
    # Draft / Slot Creation / Booking Open / Closed / Completed
    status = db.Column(db.String(20), nullable=False, default="Draft")
    instructions = db.Column(db.Text)
    results_published = db.Column(db.Boolean, default=False)

    # exam.course gives the Course; course.exams gives its exams.
    # Deleting a course also deletes its exams.
    course = db.relationship("Course", backref=db.backref("exams", cascade="all, delete-orphan"))