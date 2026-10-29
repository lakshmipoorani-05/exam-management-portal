from flask import Flask, render_template
from werkzeug.security import generate_password_hash
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


if __name__ == "__main__":
    app.run(debug=True)