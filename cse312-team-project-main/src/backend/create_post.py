from flask import Flask, request, render_template, redirect, current_app, session
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os
app = Flask(__name__, template_folder='../src/templates')

client = MongoClient("mongo", 27017)
db = client["userdata"]
userposts = db["posts"]
allowed = {'png', 'jpg', 'jpeg', 'gif'}

def process_all_posts():
    all_posts = userposts.find({})
    posts = []
    for i in all_posts:
        posts.append(i)

    return posts


def posts():
    return render_template("create_post.html")

def edit(idno):
    print("editing...", flush=True)
    print(idno, flush=True)
    user_post = userposts.find({"idno": str(idno)})

    for i in user_post:
        print(i, flush=True)
        return render_template("edit_post.html", post=i)
    
    print("Error: Post not found.", flush = True)

def make_posts():
    title = request.form['Title']
    body = request.form['body']
    picture = request.files['picture']
    user = session.get('username', '')
    idno = 0

    for i in userposts.find():
        idno += 1
    user_post = {}
    

    print("idno: " + str(idno), flush=True)
    if picture: 
        if picture.filename[picture.filename.find(".")+1:] not in allowed: 
            return render_template("create_post.html")
        picturepath = os.path.join(os.environ.get('HOME', '.'), current_app.config["UPLOAD_FOLDER"])
        picturepath = os.path.join(picturepath, secure_filename(picture.filename))
        picture.save(picturepath)
        user_post = {"title": title, "body": body, "picture": picturepath, "idno": str(idno), "user": user, "likes": 0,"liked_by":[]}
    else:
        user_post = {"title": title, "body": body, "idno": str(idno), "user": user, "likes": 0,"liked_by":[]}

    userposts.insert_one(user_post)

    return redirect("../home")

def edit_posts(idno):
    user_post = {}
    for i in userposts.find({"idno": str(idno)}):
        user_post = i
    new_post = {}
    title = request.form['Title']
    body = request.form['body']
    picture = request.files['picture']

    new_post["title"] = title
    new_post["body"] = body
    if picture: 
        if picture.filename[picture.filename.find(".")+1:] not in allowed: 
            return render_template("edit_post.html", user_post)
        picturepath = os.path.join(os.environ.get('HOME', '.'), current_app.config["UPLOAD_FOLDER"])
        picturepath = os.path.join(picturepath, secure_filename(picture.filename))
        picture.save(picturepath)
        new_post["picture"] = picturepath
    elif "picture" in user_post:
        new_post["picture"] = user_post["picture"]

    new_post["idno"] = user_post["idno"]
    new_post["user"] = user_post["user"]
    
    print(user_post, flush=True)
    print(new_post, flush=True)
    userposts.update_one({"idno": str(idno)}, {"$set": new_post})

    return redirect("/home")

def get_likes(data):

    # extract the likes from the database.
    x = userposts.find({"idno":data['_id']})
    l = 0
    for i in x:
        l = i['likes']
    return l


def update_likes(data):
    x = userposts.find({"idno":data['_id']})
    liked_by = []
    current_likes = get_likes(data)
    for i in x:
        liked_by = i['liked_by']
    if session['username'] in liked_by:
        userposts.update({"idno": (data['_id'])}, {"$set": {"likes": current_likes-1}})
        liked_by.remove(session['username'])
        userposts.update({"idno": (data['_id'])}, {"$set": {"liked_by": liked_by}})
    else:
        userposts.update({"idno": (data['_id'])}, {"$set": {"likes": current_likes+1}})
        liked_by.append(session['username'])
        userposts.update({"idno": (data['_id'])}, {"$set": {"liked_by": liked_by}})





