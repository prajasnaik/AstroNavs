from flask import Blueprint, request, jsonify, make_response, current_app
from . import create_game_manager

game_bp = Blueprint("game", __name__)
game_manager = create_game_manager()

@game_bp.route("/connect", methods=["POST"])
def connect():
    data = request.json
    client = data.get("client", "").lower()
    room_id = data.get("game_room")
    client_ip = request.remote_addr
    client_port = request.environ.get("REMOTE_PORT")

    current_app.logger.info(f"Connection attempt - Client: {client}, Room: {room_id}")

    if not client or not room_id:
        return "Missing client or game_room", 400

    if client not in current_app.config["VALID_CLIENTS"]:
        return (
            f"Invalid client type. Must be one of {current_app.config['VALID_CLIENTS']}",
            400,
        )

    room = game_manager.create_room(room_id)
    if not game_manager.add_client(room_id, client, client_ip, client_port):
        return "Game room is full", 400

    response = make_response(
        jsonify({"status": "connected", "room": room_id, "is_ready": room["is_ready"]})
    )
    response.set_cookie("client", client)
    response.set_cookie("room", room_id)
    return response


@game_bp.route("/add_safe_coordinates/<room_id>", methods=["POST"])
def add_safe_coordinates(room_id):
    client = request.cookies.get("client", "").lower()
    current_app.logger.info(
        f"Safe coordinates update attempt - Client: {client}, Room: {room_id}"
    )

    if client != "c":
        return "Only client C can set safe coordinates", 403

    room = game_manager.game_rooms.get(room_id)
    if not room:
        return "Game room not found", 404

    coordinates = request.json.get("safe_coordinates")
    if not coordinates:
        return "Missing safe_coordinates", 400

    room["safe_coordinates"] = coordinates
    room["is_running"] = True
    return jsonify({"status": "success"})


@game_bp.route("/get_game_state/<room_id>", methods=["GET"])
def get_game_state(room_id):
    current_app.logger.debug(f"Game state requested for room: {room_id}")
    state = game_manager.get_game_state(room_id)
    if not state:
        return "Game room not found", 404
    return jsonify(state)