from flask import Flask, render_template, request, make_response, redirect
from flask_socketio import SocketIO, join_room, leave_room, send
import random
from string import ascii_uppercase

app = Flask(__name__)
app.secret_key = "jadsskas"
socketio = SocketIO(app)

rooms = {}

def get_room_id(length):
    code = "".join([random.choice(ascii_uppercase) for i in range(length)])
    if code in rooms:
        get_room_id(length)
    return code


@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", 0)
        create = request.form.get("create", 0)
        print("join=",join,"create=", create)

        if create==0:
            if not code:
                return render_template("home.html", error="Please enter a room code.", code=code, name=name)
            elif code not in rooms:
                return render_template("home.html", error="Room does not exist", code=code, name=name)
            room = code

        elif join==0:
            room = get_room_id(5)
            rooms[room] = {"members": 0, "messages": []}
        
        resp = make_response(redirect("/room"))
        resp.set_cookie("name", name)
        resp.set_cookie("room", room)
        return resp

    return render_template("home.html")

@app.route("/room")
def room_func():
    room = request.cookies.get("room")
    name = request.cookies.get("name")
    if room is None or name is None or room not in rooms:
        return redirect('/')
    
    return render_template('room.html', room=room, name=name, messages=rooms[room]["messages"])

@socketio.on("connect")
def connect(auth):
    room = request.cookies.get("room")
    name = request.cookies.get("name")
    if not name or not room:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({'name': name, 'message': "has entered the room"}, to=room)
    rooms[room]["members"]+=1

@socketio.on("message")
def transmit_message(data):
    room = request.cookies.get("room")
    name = request.cookies.get("name")
    if room in rooms:
        content = {
            "name": name,
            "message": data["data"]
        }
        send(content, to=room)
        rooms[room]["messages"].append(content)

@socketio.on("disconnect")
def disconnect():
    room = request.cookies.get("room")
    name = request.cookies.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"]-=1
        if rooms[room]["members"]<=0:
            del rooms[room]
    send({'name': name, 'message': "has left the room"}, to=room)

if __name__ == "__main__":
    socketio.run(app, debug=True, port=9021)