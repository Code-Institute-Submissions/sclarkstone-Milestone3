import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_endings")
def get_endings():
    endings = mongo.db.endings.find().sort("ending_date", -1).limit(1)
    ratings = mongo.db.endings.find().sort("rating", -1).limit(1)

    return render_template("endings.html", endings=endings, ratings=ratings)


@app.route("/ending_detail/<ending_id>")
def ending_detail(ending_id):
    ending = mongo.db.endings.find_one({"_id": ObjectId(ending_id)})

    return render_template("ending_detail.html", ending=ending)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))
    
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    endings = mongo.db.endings.find({"created_by": username})

    if session["user"]:
        return render_template("profile.html", username=username, endings=endings)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_ending", methods=["GET", "POST"])
def add_ending():
    if request.method == "POST":
        ending = {
            "genre_name": request.form.get("genre_name"),
            "ending_type": request.form.get("type_name"),
            "ending_name": request.form.get("ending_name"),
            "ending_description": request.form.get("ending_description"),
            "ending_date": datetime.now(),
            "created_by": session["user"]
        }
        mongo.db.endings.insert_one(ending)
        flash("Ending Successfully Added")
        return redirect(url_for("get_endings"))

    genres = mongo.db.genres.find().sort("genre_name", 1)
    types = mongo.db.types.find().sort("type_name", 1)
    return render_template("add_ending.html", genres=genres, types=types)


@app.route("/edit_ending/<ending_id>", methods=["GET", "POST"])
def edit_ending(ending_id):
    if request.method == "POST":
        submit = {
            "genre_name": request.form.get("genre_name"),
            "ending_type": request.form.get("type_name"),
            "ending_name": request.form.get("ending_name"),
            "ending_description": request.form.get("ending_description"),
            "ending_date": datetime.now(),
            "created_by": session["user"]
        }
        mongo.db.endings.update({"_id": ObjectId(ending_id)}, submit)
        flash("Ending Successfully Updated")

    ending = mongo.db.endings.find_one({"_id": ObjectId(ending_id)})
    genres = mongo.db.genres.find().sort("genres_name", 1)
    types = mongo.db.types.find().sort("type_name", 1)
    return render_template("edit_ending.html", ending=ending, types=types, genres=genres)


@app.route("/delete_ending/<ending_id>")
def delete_ending(ending_id):
    mongo.db.endings.remove({"_id": ObjectId(ending_id)})
    flash("Ending Successfully Deleted")
    return redirect(url_for("get_endings"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)