import socket
import threading

HOST = "0.0.0.0"
PORT = 5000
BUFFER_SIZE = 1024

# Connected clients
clients = {}

# Available chat rooms
rooms = {
    "general": set()
}

# Lock for shared data
lock = threading.Lock()


def send_message(client_socket, message):
    """Send a message to one client."""

    try:
        client_socket.send(message.encode("utf-8"))
    except:
        pass


def broadcast_room(room_name, message, sender_socket=None):
    """Send a message to everyone in a room except sender."""

    with lock:
        room_members = list(
            rooms.get(room_name, set())
        )

    for client_socket in room_members:

        if client_socket != sender_socket:
            send_message(
                client_socket,
                message
            )


def get_user_room(client_socket):
    """Find the room of a client."""

    with lock:

        for room_name, members in rooms.items():

            if client_socket in members:
                return room_name

    return None


def find_user_socket(username):
    """Find socket belonging to a username."""

    with lock:

        for client_socket, name in clients.items():

            if name.lower() == username.lower():
                return client_socket

    return None


def handle_private_message(
    sender_socket,
    sender_username,
    command
):
    """
    Handle:
    /msg username message
    """

    parts = command.split(" ", 2)

    # Need username + message
    if len(parts) < 3:

        send_message(
            sender_socket,
            "[ERROR] Usage: /msg <username> <message>\n"
        )

        return

    target_username = parts[1]
    private_message = parts[2]

    # Find target user
    target_socket = find_user_socket(
        target_username
    )

    # Target not connected
    if target_socket is None:

        send_message(
            sender_socket,
            f"[ERROR] User '{target_username}' "
            "is not online.\n"
        )

        return

    # Don't allow sending to yourself
    if target_socket == sender_socket:

        send_message(
            sender_socket,
            "[ERROR] You cannot send a private "
            "message to yourself.\n"
        )

        return

    # Send to receiver
    send_message(
        target_socket,
        f"[PRIVATE] {sender_username}: "
        f"{private_message}\n"
    )

    # Confirm to sender
    send_message(
        sender_socket,
        f"[PRIVATE → {target_username}] "
        f"{private_message}\n"
    )

    print(
        f"[PRIVATE] {sender_username} "
        f"-> {target_username}: "
        f"{private_message}"
    )


def handle_client(client_socket, client_address):

    print(f"[CONNECTED] {client_address}")

    # Ask username
    send_message(
        client_socket,
        "Enter your username: "
    )

    data = client_socket.recv(BUFFER_SIZE)

    if not data:

        client_socket.close()
        return

    username = data.decode(
        "utf-8"
    ).strip()

    if not username:

        username = "Unknown"

    # Check duplicate username
    with lock:

        existing_users = [
            name.lower()
            for name in clients.values()
        ]

    if username.lower() in existing_users:

        send_message(
            client_socket,
            "[ERROR] Username already in use.\n"
        )

        client_socket.close()
        return

    # Add client
    with lock:

        clients[client_socket] = username

        rooms["general"].add(
            client_socket
        )

    print(
        f"[USER] {username} joined "
        f"from {client_address}"
    )

    # Welcome message
    send_message(
        client_socket,
        "\n================================\n"
        f"Welcome {username}!\n"
        "You are in room: general\n"
        "================================\n"
        "Commands:\n"
        "/help\n"
        "/rooms\n"
        "/users\n"
        "/join <room>\n"
        "/msg <username> <message>\n"
        "/quit\n"
        "================================\n"
    )

    broadcast_room(
        "general",
        f"[SERVER] {username} "
        "joined the general room.\n",
        client_socket
    )

    # Main communication loop
    while True:

        try:

            data = client_socket.recv(
                BUFFER_SIZE
            )

            if not data:
                break

            message = data.decode(
                "utf-8"
            ).strip()

            if not message:
                continue

            # =========================
            # HELP
            # =========================

            if message.lower() == "/help":

                send_message(
                    client_socket,
                    "\nCommands:\n"
                    "/help - Show commands\n"
                    "/rooms - Show rooms\n"
                    "/users - Show online users\n"
                    "/join <room> - Join/create room\n"
                    "/msg <user> <message> - Private message\n"
                    "/quit - Leave chat\n\n"
                )

            # =========================
            # ROOMS
            # =========================

            elif message.lower() == "/rooms":

                with lock:
                    room_names = list(
                        rooms.keys()
                    )

                room_list = "\n".join(
                    f"- {room}"
                    for room in room_names
                )

                send_message(
                    client_socket,
                    f"\nAvailable rooms:\n"
                    f"{room_list}\n\n"
                )

            # =========================
            # USERS
            # =========================

            elif message.lower() == "/users":

                with lock:

                    online_users = list(
                        clients.values()
                    )

                user_list = "\n".join(
                    f"- {user}"
                    for user in online_users
                )

                send_message(
                    client_socket,
                    f"\nOnline users:\n"
                    f"{user_list}\n\n"
                )

            # =========================
            # PRIVATE MESSAGE
            # =========================

            elif message.lower().startswith(
                "/msg "
            ):

                handle_private_message(
                    client_socket,
                    username,
                    message
                )

            # =========================
            # JOIN ROOM
            # =========================

            elif message.lower().startswith(
                "/join "
            ):

                new_room = message[
                    6:
                ].strip().lower()

                if not new_room:

                    send_message(
                        client_socket,
                        "[ERROR] Usage: "
                        "/join <room>\n"
                    )

                    continue

                old_room = get_user_room(
                    client_socket
                )

                with lock:

                    # Create room
                    if new_room not in rooms:

                        rooms[new_room] = set()

                    # Leave old room
                    if (
                        old_room
                        and client_socket
                        in rooms[old_room]
                    ):

                        rooms[old_room].remove(
                            client_socket
                        )

                    # Join new room
                    rooms[new_room].add(
                        client_socket
                    )

                if old_room:

                    broadcast_room(
                        old_room,
                        f"[SERVER] {username} "
                        f"left {old_room}.\n"
                    )

                send_message(
                    client_socket,
                    f"[SERVER] You joined "
                    f"room: {new_room}\n"
                )

                broadcast_room(
                    new_room,
                    f"[SERVER] {username} "
                    f"joined {new_room}.\n",
                    client_socket
                )

                print(
                    f"[ROOM] {username}: "
                    f"{old_room} -> {new_room}"
                )

            # =========================
            # QUIT
            # =========================

            elif message.lower() == "/quit":

                send_message(
                    client_socket,
                    "Goodbye!\n"
                )

                break

            # =========================
            # NORMAL MESSAGE
            # =========================

            else:

                current_room = get_user_room(
                    client_socket
                )

                if current_room:

                    print(
                        f"[{current_room}] "
                        f"{username}: "
                        f"{message}"
                    )

                    broadcast_room(
                        current_room,
                        f"[{current_room}] "
                        f"{username}: "
                        f"{message}\n",
                        client_socket
                    )

        except Exception as error:

            print(
                f"[ERROR] {username}: "
                f"{error}"
            )

            break

    # =============================
    # CLIENT DISCONNECTED
    # =============================

    current_room = get_user_room(
        client_socket
    )

    with lock:

        if current_room:

            rooms[
                current_room
            ].discard(
                client_socket
            )

        if client_socket in clients:

            del clients[
                client_socket
            ]

    print(
        f"[DISCONNECTED] {username}"
    )

    if current_room:

        broadcast_room(
            current_room,
            f"[SERVER] {username} "
            f"left {current_room}.\n"
        )

    client_socket.close()


def main():

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server_socket.bind(
        (HOST, PORT)
    )

    server_socket.listen(10)

    print("===================================")
    print("      MULTI-CLIENT CHAT SERVER")
    print("===================================")
    print(f"Server listening on port {PORT}")
    print("Default room: general")
    print("Waiting for clients...\n")

    while True:

        client_socket, client_address = (
            server_socket.accept()
        )

        client_thread = threading.Thread(
            target=handle_client,
            args=(
                client_socket,
                client_address
            )
        )

        client_thread.daemon = True

        client_thread.start()


if __name__ == "__main__":
    main()
