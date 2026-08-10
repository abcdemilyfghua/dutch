from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
import uuid
from Round import Round
from RandomAI import Mordna

app = FastAPI()
rooms = {}

async def send_to_player(room, player_name, message):
    ws = room["connections"].get(player_name)
    if ws is not None:
            await ws.send_json(message)

async def broadcast(room, message):
    for ws in room["connections"].values():
        await ws.send_json(message)

@app.post("/rooms")
def create_room():
    room_id = str(uuid.uuid4())
    rooms[room_id] = {"players": [], "agents": {}, "round": None, "connections": {}, "pending_draw": None}
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

@app.websocket("/rooms/{room_id}/ws/{player_name}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_name: str):
    await websocket.accept()

    if room_id not in rooms:
        await websocket.close(code=1008, reason="Room not found")
        return

    room = rooms[room_id]
    room["connections"][player_name] = websocket

    try:
        while True:
            data = await websocket.receive_json()
            r = room["round"]

            current = r.players[r.current_turn]
            if player_name != current:
                await send_to_player(room, player_name, {"error": "not your turn"})
                continue

            if data["action"] == "draw":
                drawn = r.draw_card()
                room["pending_draw"] = drawn
                await send_to_player(room, player_name, {"action": "draw_result", "card": str(drawn)})
                await broadcast(room, {"action": "draw", "player": player_name})

            elif data["action"] == "swap":
                pos = data["position"]
                discarded = r.resolve_draw(room["pending_draw"], swap_position=pos)
                room["pending_draw"] = None
                await broadcast(room, {"action": "discarded_result", "card": str(discarded)})

            elif data["action"] == "discard":
                discarded = r.resolve_draw(room["pending_draw"], swap_position=None)
                room["pending_draw"] = None
                await broadcast(room, {"action": "discarded_result", "card": str(discarded)})

    except WebSocketDisconnect:
        room["connections"].pop(player_name, None)