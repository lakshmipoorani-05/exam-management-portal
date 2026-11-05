from datetime import datetime
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
    examiners = db.relationship("User", secondary="exam_examiners", backref="assigned_exams")
    
class Rubric(db.Model):
    __tablename__ = "rubrics"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    criterion = db.Column(db.String(150), nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    weightage = db.Column(db.Float, nullable=False, default=1)
    description = db.Column(db.Text)

    # deleting an exam also deletes its rubric criteria
    exam = db.relationship("Exam", backref=db.backref("rubrics", cascade="all, delete-orphan"))

    # link table: one exam can have many examiners, and one examiner many exams
exam_examiners = db.Table(
    "exam_examiners",
    db.Column("exam_id", db.Integer, db.ForeignKey("exams.id"), primary_key=True),
    db.Column("examiner_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
)

class Slot(db.Model):
    __tablename__ = "slots"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    slot_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    available = db.Column(db.Integer, nullable=False)   # seats left
    venue = db.Column(db.String(150))
    status = db.Column(db.String(20), nullable=False, default="Available")  # Available / Full / Cancelled / Completed

    exam = db.relationship("Exam", backref=db.backref("slots", cascade="all, delete-orphan"))
    examiner = db.relationship("User", backref="slots")

class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("slots.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), nullable=False, default="Booked")  # Booked / Cancelled / Completed
    # filled in when the examiner evaluates (next phase)
    total_marks = db.Column(db.Float)
    remarks = db.Column(db.Text)
    evaluated_at = db.Column(db.DateTime)

    student = db.relationship("User", backref="bookings")
    slot = db.relationship("Slot", backref=db.backref("bookings", cascade="all, delete-orphan"))
    exam = db.relationship("Exam", backref=db.backref("bookings", cascade="all, delete-orphan"))

class Evaluation(db.Model):
    """One mark for one rubric criterion for one booking."""
    __tablename__ = "evaluations"

    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), primary_key=True)
    rubric_id = db.Column(db.Integer, db.ForeignKey("rubrics.id"), primary_key=True)
    marks = db.Column(db.Float, nullable=False)

    booking = db.relationship("Booking", backref=db.backref("evaluations", cascade="all, delete-orphan"))
    rubric = db.relationship("Rubric", backref=db.backref("evaluations", cascade="all, delete-orphan"))