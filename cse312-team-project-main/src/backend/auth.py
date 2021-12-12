from functools import wraps
from flask import Flask, request, render_template, redirect, session
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
from .create_post import process_all_posts

app = Flask(__name__, template_folder='../src/templates')
client = MongoClient("mongo", 27017)
db = client["userdata"]
registerUser = db["register"]

allUsers = set()
onlineUsers = set()

themes = {"light": "#398ce3", "dark": "#0a3663"}

def homepage():
    all_posts = process_all_posts()
    return render_template("homepage.html", content=all_posts, room=session.get('id'))


class User:

    def register(self):
        if request.method == "GET":
            return render_template("register.html")
        elif request.method == "POST":
            username = request.form['uname']
            password = request.form['pswd']
            theme = themes[request.form["bg"]]
            # Retrieve from database
            x = registerUser.find_one({"username": username})
            # Check for username availability
            if x is not None:
                if x["username"] == username:
                    return "This username is already taken"
            # Insert into database
            userData = {"username": username, "password": generate_password_hash(password), "theme": theme}
            registerUser.insert_one(userData)
            # Retrieve data or session
            user = registerUser.find_one({"username": username})
            uid = str(user["_id"])
            return self.start_session(uid, username, theme)

    def login(self):
        if request.method == "GET":
            return render_template("login.html")
        elif request.method == "POST":
            # If form submitted
            # if username and password is None:
            username = request.form['uname']
            password = request.form['pswd']
            # Retrieve from database
            user = registerUser.find_one({"username": username})

            # Check existence of username
            if user is not None:
                # Check password to be correct
                if not check_password_hash(user["password"], password):
                    return "Please enter the correct username or password."
            else:
                return "Please enter the correct username or password."

            # Else function call after registration or successful login
            uid = str(user["_id"])
            theme = user["theme"]
            return self.start_session(uid, username, theme)

    def handleThemeChange(self):
        if request.method == "GET":
            return render_template("theme.html", room=session.get('id'))
        elif request.method == "POST":
            user = session["username"]
            newTheme = themes[request.form["bg"]]
            session["theme"] = newTheme

            registerUser.update_one({"username": user}, {"$set": {"theme": newTheme}})
            return redirect("../home")

    def start_session(self, uid, username, theme):
        if uid is not None:
            allUsers.add(username)
            onlineUsers.add(username)
            session["logged_in"] = True
            session["id"] = uid
            session["username"] = username
            session["theme"] = theme
            session['room'] = 'chat'
            return redirect("../home")
        else:
            return redirect("../")

    def logout(self):
        onlineUsers.remove(session["username"])
        session.clear()
        return redirect("../")


# Decorator
def login_required(view):
    @wraps(view)
    def wrap(*arg, **kwargs):
        if "logged_in" in session:
            return view(*arg, **kwargs)
        else:
            return redirect("../")

    return wrap
