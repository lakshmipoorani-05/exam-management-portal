from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, session, g, abort)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from model import db, User, Course, Exam
app = Flask(__name__)
app.secret_key = "change-this-later"

# sqlite:/// means a SQLite file; Flask-SQLAlchemy puts it in an "instance" folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///emp.db"

# connect the db object from model.py to this Flask app
db.init_app(app)


def init_db():
    db.create_all()  # creates every table defined in model.py (only if missing)
    # the admin must already exist, because admins cannot register
    if not User.query.filter_by(role="admin").first():
        admin = User(
            name="Administrator",
            email="admin@emp.com",
            password=generate_password_hash("admin123"),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()


with app.app_context():
    init_db()


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        role = request.form["role"]

        # backend validation: never trust the browser alone
        if role not in ("student", "examiner"):
            flash("Please choose a valid role.", "danger")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("This email is already registered.", "danger")
        else:
            # examiners must wait for admin approval, students are active at once
            status = "pending" if role == "examiner" else "active"
            user = User(
                name=name,
                email=email,
                password=generate_password_hash(password),
                role=role,
                phone=request.form.get("phone"),
                department=request.form.get("department"),
                roll_no=request.form.get("roll_no"),
                status=status,
            )
            db.session.add(user)
            db.session.commit()
            flash("Registration successful.", "success")
            return redirect(url_for("index"))

    return render_template("register.html")

@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id else None
    if g.user is not None and g.user.status == "deactivated":
        session.clear()
        g.user = None

def role_required(role):
    """Only let users with this role into the page."""
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if g.user is None:
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
            if g.user.role != role:
                abort(403)  # logged in, but the wrong role
            if role == "examiner" and g.user.status != "active":
                return render_template("pending.html")  # not approved yet
            return view(*args, **kwargs)
        return wrapper
    return decorator

EXAM_TYPES = ["Viva", "Practical", "Project Demo", "Assessment"]


def parse_date(text):
    return datetime.strptime(text, "%Y-%m-%d").date()


def read_exam_form(form):
    """Read and validate the exam form. Returns (values, error_message)."""
    try:
        values = {
            "course_id": int(form["course_id"]),
            "name": form["name"].strip(),
            "exam_type": form["exam_type"],
            "duration": int(form["duration"]),
            "max_marks": int(form["max_marks"]),
            "slot_create_start": parse_date(form["slot_create_start"]),
            "slot_create_end": parse_date(form["slot_create_end"]),
            "booking_start": parse_date(form["booking_start"]),
            "booking_end": parse_date(form["booking_end"]),
            "instructions": form.get("instructions"),
        }
    except (ValueError, KeyError):
        return None, "Please fill every field with valid values."

    if db.session.get(Course, values["course_id"]) is None:
        return None, "Please choose a valid course."
    if values["exam_type"] not in EXAM_TYPES:
        return None, "Please choose a valid exam type."
    if values["duration"] < 1 or values["max_marks"] < 1:
        return None, "Duration and maximum marks must be at least 1."
    if values["slot_create_end"] < values["slot_create_start"]:
        return None, "Slot creation end date cannot be before its start date."
    if values["booking_end"] < values["booking_start"]:
        return None, "Booking end date cannot be before its start date."
    return values, None

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        user = User.query.filter_by(email=email).first()

        if user is None or not check_password_hash(user.password, request.form["password"]):
            flash("Invalid email or password.", "danger")
        elif user.status == "deactivated":
            flash("Your account has been deactivated.", "danger")
        else:
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    # send each user to the dashboard for their own role
    if g.user is None:
        return redirect(url_for("login"))
    return redirect(url_for(g.user.role + "_dashboard"))


@app.route("/admin")
@role_required("admin")
def admin_dashboard():
    stats = {
        "Courses": Course.query.count(),
        "Examinations": Exam.query.count(),
        "Examiners": User.query.filter_by(role="examiner").count(),
        "Students": User.query.filter_by(role="student").count(),
    }
    pending = User.query.filter_by(role="examiner", status="pending").count()
    return render_template("admin_dashboard.html", stats=stats, pending=pending)


@app.route("/admin/students")
@role_required("admin")
def admin_students():
    students = User.query.filter_by(role="student").order_by(User.id.desc()).all()
    return render_template("admin_students.html", students=students)


@app.route("/examiner")
@role_required("examiner")
def examiner_dashboard():
    return render_template("examiner_dashboard.html")


@app.route("/student")
@role_required("student")
def student_dashboard():
    return render_template("student_dashboard.html")


@app.errorhandler(403)
def forbidden(error):
    return render_template("error.html", code=403, message="You do not have access to this page."), 403

@app.route("/admin/examiners")
@role_required("admin")
def admin_examiners():
    examiners = User.query.filter_by(role="examiner").order_by(User.id.desc()).all()
    return render_template("admin_examiners.html", examiners=examiners)


@app.route("/admin/examiners/add", methods=["GET", "POST"])
@role_required("admin")
def admin_add_examiner():
    # the admin creates an examiner who is approved straight away
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("This email is already registered.", "danger")
        else:
            examiner = User(
                name=request.form["name"].strip(),
                email=email,
                password=generate_password_hash(password),
                role="examiner",
                phone=request.form.get("phone"),
                department=request.form.get("department"),
                status="active",
            )
            db.session.add(examiner)
            db.session.commit()
            flash("Examiner added and approved.", "success")
            return redirect(url_for("admin_examiners"))
    return render_template("admin_examiner_form.html")


@app.route("/admin/examiners/<int:user_id>/<action>", methods=["POST"])
@role_required("admin")
def admin_examiner_action(user_id, action):
    examiner = db.session.get(User, user_id)
    if examiner is None or examiner.role != "examiner":
        abort(404)
    new_status = {"approve": "active", "deactivate": "deactivated", "activate": "active"}.get(action)
    if new_status is None:
        abort(400)
    examiner.status = new_status
    db.session.commit()
    flash(f"{examiner.name} is now {new_status}.", "success")
    return redirect(url_for("admin_examiners"))

@app.route("/admin/courses")
@role_required("admin")
def admin_courses():
    courses = Course.query.order_by(Course.code).all()
    return render_template("admin_courses.html", courses=courses)


@app.route("/admin/courses/new", methods=["GET", "POST"])
@role_required("admin")
def admin_course_new():
    if request.method == "POST":
        code = request.form["code"].strip().upper()
        if Course.query.filter_by(code=code).first():
            flash("A course with this code already exists.", "danger")
        else:
            course = Course(
                code=code,
                name=request.form["name"].strip(),
                description=request.form.get("description"),
                credits=int(request.form.get("credits") or 3),
                status=request.form.get("status", "Active"),
            )
            db.session.add(course)
            db.session.commit()
            flash("Course created.", "success")
            return redirect(url_for("admin_courses"))
    return render_template("admin_course_form.html", course=None)


@app.route("/admin/courses/<int:course_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def admin_course_edit(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    if request.method == "POST":
        code = request.form["code"].strip().upper()
        clash = Course.query.filter(Course.code == code, Course.id != course.id).first()
        if clash:
            flash("Another course already uses this code.", "danger")
        else:
            course.code = code
            course.name = request.form["name"].strip()
            course.description = request.form.get("description")
            course.credits = int(request.form.get("credits") or 3)
            course.status = request.form.get("status", "Active")
            db.session.commit()
            flash("Course updated.", "success")
            return redirect(url_for("admin_courses"))
    return render_template("admin_course_form.html", course=course)


@app.route("/admin/courses/<int:course_id>/delete", methods=["POST"])
@role_required("admin")
def admin_course_delete(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)
    db.session.delete(course)
    db.session.commit()
    flash("Course removed.", "info")
    return redirect(url_for("admin_courses"))

@app.route("/admin/exams")
@role_required("admin")
def admin_exams():
    exams = Exam.query.order_by(Exam.id.desc()).all()
    return render_template("admin_exams.html", exams=exams)


@app.route("/admin/exams/new", methods=["GET", "POST"])
@role_required("admin")
def admin_exam_new():
    courses = Course.query.filter_by(status="Active").order_by(Course.code).all()
    if request.method == "POST":
        values, error = read_exam_form(request.form)
        if error:
            flash(error, "danger")
        else:
            db.session.add(Exam(**values))
            db.session.commit()
            flash("Examination created.", "success")
            return redirect(url_for("admin_exams"))
    return render_template("admin_exam_form.html", exam=None, courses=courses, exam_types=EXAM_TYPES)


@app.route("/admin/exams/<int:exam_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def admin_exam_edit(exam_id):
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        abort(404)
    courses = Course.query.filter_by(status="Active").order_by(Course.code).all()
    if request.method == "POST":
        values, error = read_exam_form(request.form)
        if error:
            flash(error, "danger")
        else:
            for field, value in values.items():
                setattr(exam, field, value)
            db.session.commit()
            flash("Examination updated.", "success")
            return redirect(url_for("admin_exams"))
    return render_template("admin_exam_form.html", exam=exam, courses=courses, exam_types=EXAM_TYPES)


@app.route("/admin/exams/<int:exam_id>/delete", methods=["POST"])
@role_required("admin")
def admin_exam_delete(exam_id):
    exam = db.session.get(Exam, exam_id)
    if exam is None:
        abort(404)
    db.session.delete(exam)
    db.session.commit()
    flash("Examination removed.", "info")
    return redirect(url_for("admin_exams"))

if __name__ == "__main__":
    app.run(debug=True)