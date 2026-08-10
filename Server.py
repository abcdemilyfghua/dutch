from fastapi import FastAPI, HTTPException
import uuid
from Round import Round
from RandomAI import Mordna

app = FastAPI()
rooms = {}

@app.post("/rooms")
def create_room():
    room_id = str(uuid.uuid4())
    rooms[room_id] = {"players": [], "agents": {}, "round": None}
    return {"room_id": room_id}

@app.post("/rooms/{room_id}/join")
def join_room(room_id: str, name: str, is_ai: bool = False):
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    room = rooms[room_id]

    if is_ai:
        name = "Mordna"
        counter = 2
        while name in room["players"]:
            name = f"Mordna {counter}"
            counter += 1
        room["agents"][name] = Mordna()
    else:
        if name in room["players"]:
            raise HTTPException(status_code=400, detail="Name taken")
        room["agents"][name] = None

    room["players"].append(name)
    return {"players": room["players"]}


@app.post("/rooms/{room_id}/start")
def start_room(room_id: str):
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    room = rooms[room_id]

    if len(room["players"]) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 players to start")

    new_round = Round(room["players"])
    room["round"] = new_round

    return "The game has started."