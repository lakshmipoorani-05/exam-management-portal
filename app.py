from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   flash, session, g, abort)
from werkzeug.security import generate_password_hash, check_password_hash
from model import db, User

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
    # runs before every request; g.user is the logged-in user, or None
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id else None

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
    return render_template("admin_dashboard.html")


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

if __name__ == "__main__":
    app.run(debug=True)