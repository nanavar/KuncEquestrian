import hashlib
import uuid
import requests
import datetime

from flask import Flask, render_template, request, make_response, redirect, url_for
from models import User, Message, db
from sqlalchemy_pagination import paginate

app = Flask(__name__)

db.create_all()


@app.route("/")
def index():
    session_token = request.cookies.get("session_token")
    city = "Ljubljana"
    apikey = "5aee9c3477da8da19e35522887956dc7"
    unit = "metric"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={apikey}&units={unit}"

    data = requests.get(url=url)

    if session_token:
        user = db.query(User).filter_by(session_token=session_token).first()
    else:
        user = None

    return render_template("index.html", user=user, data=data.json())


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("user-name")
    email = request.form.get("user-email")
    password = request.form.get("user-password")
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    user = db.query(User).filter_by(email=email).first()

    if not user:
        user = User(name=name, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()

    if hashed_password != user.password:
        return "WRONG PASSWORD"

    session_token = str(uuid.uuid4())
    user.session_token = session_token
    db.session.add(user)
    db.session.commit()

    response = make_response(redirect(url_for('profile')))
    response.set_cookie("session_token", session_token, httponly=True, samesite='strict')

    return response


@app.route("/messages")
def messages():
    page = request.args.get("page")

    if not page:
        page = 1
    messages_query = db.query(Message)
    messages = paginate(messages_query, page=int(page), page_size=5)
    return render_template('messages.html', messages=messages)


@app.route("/add-message", methods=["POST"])
def add_message():
    name = request.form.get('name')
    message = request.form.get('message')
    message = Message(name=name, text=message)
    db.session.add(message)
    db.session.commit()

    return redirect("messages")


@app.route("/profile", methods=["GET"])
def profile():
    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token).first()

    if user:
        return render_template("profile.html", user=user)
    else:
        return redirect(url_for("login"))


@app.route("/horses")
def horses():
    return render_template("horses.html")


if __name__ == '__main__':
    app.run(use_reloader=True, debug=True)
