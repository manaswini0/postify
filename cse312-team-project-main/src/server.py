from flask import Flask, send_file, render_template, session, url_for
from backend import auth, create_post, chat_room
from backend.chat_room import *
from flask_socketio import SocketIO, join_room, leave_room, emit
from os import path

app = Flask(__name__, template_folder='../src/templates')
app.secret_key = "Postify"
socketio = SocketIO(app)

app.config.from_mapping(
        UPLOAD_FOLDER='src/backend/images/',
    )


@app.route("/")
def landing():
    return render_template("index.html")


@app.route("/style.css")
def style():
    return send_file(url_for('static', filename='style.css'))


@app.route("/home", methods=['GET'])
@auth.login_required
def home():
    return auth.homepage()


@app.route("/online")
@auth.login_required
def display():
    return render_template("online.html", online=auth.onlineUsers, offline=auth.allUsers-auth.onlineUsers)


@app.route('/root/src/backend/images/<path:filename>')
def getImage(filename):
    extension = filename[filename.find(".")+1:]
    return send_file(path.join("backend/images/", filename), mimetype=extension)


@app.route("/auth/<action>", methods=['POST', 'GET'])
def process(action):
    if action == "register":
        return auth.User().register()
    elif action == "login":
        return auth.User().login()
    elif action == "logout":
        return auth.User().logout()


@app.route("/change-theme", methods=['POST', 'GET'])
@auth.login_required
def changeTheme():
    return auth.User().handleThemeChange()


@app.route('/blog/edit/<idno>', methods=['POST', 'GET'])
@auth.login_required
def edit(idno):
    return create_post.edit(idno)


@app.route('/blog/edit_post/<idno>', methods=['POST', 'GET'])
@auth.login_required
def edit_post(idno):
    return create_post.edit_posts(idno)


@app.route('/blog/<action>', methods=['POST', 'GET'])
@auth.login_required
def create(action):
    if action == "create":
        return create_post.posts()
    elif action == "create_post":
        return create_post.make_posts()

@app.route('/chat/<user>/')
@auth.login_required
def chat_room(user):
    if user != session.get('username'):
        userRoom = userLookup(user)
        if userRoom is not None:
            print(userRoom, flush=True)
            room = fetchRoom(session.get('username'), user)
            if room != "":
                print("room exists", flush=True)
                return render_template('chat_room.html', room=room,
                                        mID=userRoom, member=user)
            else:
                print("new room", flush=True)
                room = createRoom(user)
                return render_template('chat_room.html', room=room,
                                        mID=userRoom, member=user)
        else:
            return "Requested user does not exist. You can only message registered users."
    else:
       return "You may only send direct messages to other users, and not to yourself." 


@socketio.on('join')
def join(message):
    room = message.get("room")
    join_room(room)
    print(message.get("user") + ' has entered the chat.', flush=True)
    if room != session.get('id'):
        emit("joined", {'sender': message.get('user'), 'message': 'has entered the chat.'}, broadcast=True, room=room)


@socketio.on('message')
def send(message):
    # room = message.get("room")
    # payload = message.get('username') + ":" + message.get('message')
    emit("message", {'sender': message.get('user'), 
        'message': message.get('message')}, broadcast=True,
         room=message.get('room'))
    print(message.get('mID'), flush=True)
    print('sending to notif socket', flush=True)
    emit('notif', {'sender': message.get('user'),
            'message': message.get('message'), 'redirect': message.get('user')},
            room=message.get('mID'))


@socketio.on('leave')
def leave(message):
    room = message.get("room")
    emit("joined", {'sender': message.get('user'), 'message': 'has left the chat.'}, broadcast=True, room=room)
    leave_room(room)
    


@socketio.on('like event')
def like_event(data):
    create_post.update_likes(data)
    current_likes = create_post.get_likes(data)
    data['data'] = current_likes
    emit("from server", data, broadcast=True)



if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)
