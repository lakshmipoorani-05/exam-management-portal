from flask import Flask, render_template, request, redirect, url_for, flash, session, g
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
    if g.user is None:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)