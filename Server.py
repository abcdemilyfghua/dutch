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

async def advance_and_check(room):
    r = room["round"]
    r.advance_turn()
    if r.is_round_over():
        totals, winner = r.score()
        await broadcast(room, {"action": "round_over", "totals": totals, "winner": winner})
    else:
        await play_ai_turns(room)

async def play_ai_turns(room):
    r = room["round"]
    while not r.is_round_over():
        current = r.players[r.current_turn]
        agent = room["agents"][current]
        if agent is None:
            return  # it's a human's turn now — stop, wait for their message

        if agent.decide_dutch():
            r.call_dutch()
            await broadcast(room, {"action": "dutch_called", "player": current})
        else:
            drawn = r.draw_card()
            await broadcast(room, {"action": "draw", "player": current})
            pos = agent.decide_swap_position()
            discarded = r.resolve_draw(drawn, swap_position=pos)
            await broadcast(room, {"action": "discarded_result", "card": str(discarded)})

            if discarded.rank in ("J", "Q"):
                if agent.decide_use_ability():
                    (pos_a_player, pos_a, pos_b_player, pos_b) = agent.decide_targets(room["players"])                

                    if discarded.rank == "J":
                        r.play_jack(pos_a_player, pos_a, pos_b_player, pos_b)
                        await broadcast(room, {"action": "jack_swap", "player": current,
                            "target1_player": pos_a_player, "target1_pos": pos_a,
                            "target2_player": pos_b_player, "target2_pos": pos_b})

                    if discarded.rank == "Q":
                        r.play_queen(pos_a_player, pos_a, pos_b_player, pos_b)
                        await broadcast(room, {"action": "queen_peek", "player": current,
                            "target1_player": pos_a_player, "target1_pos": pos_a,
                            "target2_player": pos_b_player, "target2_pos": pos_b})

        r.advance_turn()

    totals, winner = r.score()
    await broadcast(room, {"action": "round_over", "totals": totals, "winner": winner})

@app.post("/rooms")
def create_room():
    room_id = str(uuid.uuid4())
    rooms[room_id] = {"players": [], "agents": {}, "round": None, "connections": {}, "pending_draw": None, "last_discarded": None, "awaiting_ability": False}
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
async def start_room(room_id: str):
    if room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    room = rooms[room_id]

    if len(room["players"]) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 players to start")

    new_round = Round(room["players"])
    room["round"] = new_round
    await play_ai_turns(room)
    return "The game has started."

@app.websocket("/rooms/{room_id}/ws/{player_name}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_name: str):
    await websocket.accept()

    if room_id not in rooms:
        await websocket.close(code=1008, reason="Room not found")
        return

    room = rooms[room_id]
    room["connections"][player_name] = websocket
    await send_to_player(room, player_name, {"action": "room_state", "connected_players": list(room["connections"].keys())})
    await broadcast(room, {"action": "player_connected", "player": player_name})

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
                if not (0 <= pos <= 3):
                    await send_to_player(room, player_name, {"error": "invalid position"})
                    continue
                discarded = r.resolve_draw(room["pending_draw"], swap_position=pos)
                room["last_discarded"] = discarded
                room["pending_draw"] = None
                await broadcast(room, {"action": "discarded_result", "card": str(discarded)})
                if discarded.rank not in ("J", "Q"):
                    await advance_and_check(room)
                else:
                    room["awaiting_ability"] = True

            elif data["action"] == "discard":
                discarded = r.resolve_draw(room["pending_draw"], swap_position=None)
                room["last_discarded"] = discarded
                room["pending_draw"] = None
                await broadcast(room, {"action": "discarded_result", "card": str(discarded)})
                if discarded.rank not in ("J", "Q"):
                    await advance_and_check(room)
                else:
                    room["awaiting_ability"] = True

            elif data["action"] == "use_ability":
                if room["awaiting_ability"] == False:
                    await send_to_player(room, player_name, {"error": "there is no ability to be used here"})
                    continue
                else:
                    pos_a_player = data["target1_player"]
                    pos_a = data["target1_pos"]
                    pos_b_player = data["target2_player"]
                    pos_b = data["target2_pos"]

                    if pos_a_player not in room["players"] or pos_b_player not in room["players"]:
                        await send_to_player(room, player_name, {"error": "invalid target player"})
                        continue
                    if not (0 <= pos_a <= 3) or not (0 <= pos_b <= 3):
                        await send_to_player(room, player_name, {"error": "invalid position"})
                        continue

                    if room["last_discarded"].rank == "J":
                        r.play_jack(pos_a_player, pos_a, pos_b_player, pos_b)
                        await broadcast(room, {"action": "jack_swap", "player": player_name,
                            "target1_player": pos_a_player, "target1_pos": pos_a,
                            "target2_player": pos_b_player, "target2_pos": pos_b})
                        
                    elif room["last_discarded"].rank == "Q":
                        peeked = r.play_queen(pos_a_player, pos_a, pos_b_player, pos_b)
                        await send_to_player(room, player_name, {"action": "queen_peek_result", "cards": [str(peeked[0]), str(peeked[1])]})
                        await broadcast(room, {"action": "queen_peek", "player": player_name,
                            "target1_player": pos_a_player, "target1_pos": pos_a,
                            "target2_player": pos_b_player, "target2_pos": pos_b})

                    room["awaiting_ability"] = False
                    
                await advance_and_check(room)

            elif data["action"] == "skip_ability":
                if room["awaiting_ability"] == False:
                    await send_to_player(room, player_name, {"error": "there is no ability to be used here"})
                    continue
                room["awaiting_ability"] = False
                await advance_and_check(room)

            elif data["action"] == "call_dutch":
                r.call_dutch()
                await broadcast(room, {"action": "dutch_called", "player": player_name})
                await advance_and_check(room)

    except WebSocketDisconnect:
        room["connections"].pop(player_name, None)