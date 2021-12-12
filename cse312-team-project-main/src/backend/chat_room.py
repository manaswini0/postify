from functools import wraps
from flask import Flask, request, render_template, redirect, session
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
from .create_post import process_all_posts

app = Flask(__name__, template_folder='../src/templates')
client = MongoClient("mongo", 27017)
db = client["userdata"]
registerUser = db["register"]


chat_db = client["user_rooms"]
active_rooms = chat_db["active_rooms"]



def fetchRoom(user, target):
    room = ""
    user_rooms = chat_db[session.get('username')]
    entry = user_rooms.find_one({'target': target})
    if entry != None:
        room = entry['room_id']
    return room


def createRoom(target):
    user_rooms = chat_db[session.get('username')]
    target_rooms = chat_db[str(target)]

    room_id = active_rooms.insert_one({"members": str([session.get('username'), target])}).inserted_id
    roomEntry = {"target": str(target), "room_id": room_id}
    targetEntry = {"target": str(session.get('username')), "room_id": room_id}
    user_rooms.insert_one(roomEntry)
    target_rooms.insert_one(targetEntry)
    return room_id

def userLookup(target):
    #this function will check to see if a targeted user is registered
    #if this function returns false, a chatroom cannot be created with that user
    user = registerUser.find_one({"username": target})
    if user is not None:
        return user["_id"]
    else:
        return None






