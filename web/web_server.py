import asyncio
import json
import websockets

# ============================================================
# WEB <-> TCP CHAT BRIDGE
# Username only - no password
# ============================================================

TCP_HOST = "10.0.0.4"
TCP_PORT = 5000

WEBSOCKET_HOST = "0.0.0.0"
WEBSOCKET_PORT = 8765

connected_clients = {}


async def send_json(websocket, data):
    try:
        await websocket.send(json.dumps(data))
    except Exception:
        pass


async def broadcast_users():
    users = sorted(
        info["username"]
        for info in connected_clients.values()
    )

    dead = []

    for ws in list(connected_clients):
        try:
            await ws.send(json.dumps({
                "type": "users",
                "users": users
            }))
        except Exception:
            dead.append(ws)

    for ws in dead:
        connected_clients.pop(ws, None)


async def connect_tcp(username):
    try:
        reader, writer = await asyncio.open_connection(
            TCP_HOST,
            TCP_PORT
        )

        print(
            f"[TCP CONNECTED] {username} -> "
            f"{TCP_HOST}:{TCP_PORT}"
        )

        # The TCP server asks for the username first.
        prompt = await reader.read(4096)

        print(
            f"[TCP -> WEB] {username}: "
            f"{prompt.decode(errors='replace')}"
        )

        writer.write((username + "\n").encode("utf-8"))
        await writer.drain()

        return reader, writer

    except Exception as error:
        print(
            f"[TCP CONNECTION ERROR] {username}: {error}"
        )
        return None, None


async def read_tcp_server(websocket, reader, username):
    try:
        while True:
            data = await reader.read(4096)

            if not data:
                break

            message = data.decode(
                "utf-8",
                errors="replace"
            )

            print(
                f"[TCP -> WEB] {username}: {message}"
            )

            # Never forward the initial username prompt.
            if message.strip() == "Enter your username:":
                continue

            await websocket.send(message)

    except asyncio.CancelledError:
        pass

    except Exception as error:
        print(
            f"[TCP READER ERROR] {username}: {error}"
        )


async def handle_browser(websocket):
    username = None
    reader = None
    writer = None
    reader_task = None

    print("[WEB CONNECTED]")

    try:
        first_message = await websocket.recv()

        try:
            request = json.loads(first_message)
        except json.JSONDecodeError:
            await send_json(websocket, {
                "type": "join_error",
                "message": "Invalid join request."
            })
            return

        if request.get("type") != "join":
            await send_json(websocket, {
                "type": "join_error",
                "message": "Please enter a username."
            })
            return

        username = str(
            request.get("username", "")
        ).strip()

        if not username:
            await send_json(websocket, {
                "type": "join_error",
                "message": "Username is required."
            })
            return

        # Prevent the same username from being connected twice.
        if any(
            info["username"].lower() == username.lower()
            for info in connected_clients.values()
        ):
            await send_json(websocket, {
                "type": "join_error",
                "message": "Username is already online."
            })
            return

        reader, writer = await connect_tcp(username)

        if reader is None:
            await send_json(websocket, {
                "type": "join_error",
                "message": "Chat server is not available."
            })
            return

        connected_clients[websocket] = {
            "username": username,
            "reader": reader,
            "writer": writer
        }

        await send_json(websocket, {
            "type": "join_success",
            "username": username,
            "room": "general"
        })

        await broadcast_users()

        reader_task = asyncio.create_task(
            read_tcp_server(
                websocket,
                reader,
                username
            )
        )

        while True:
            message = await websocket.recv()

            if message is None:
                break

            message = str(message).strip()

            if not message:
                continue

            # Frontend asks for the current online-user list.
            if message == "__GET_USERS__":
                users = sorted(
                    info["username"]
                    for info in connected_clients.values()
                )

                await send_json(websocket, {
                    "type": "users",
                    "users": users
                })
                continue

            # Everything else is a normal TCP chat command/message.
            print(
                f"[WEB -> TCP] {username}: {message}"
            )

            writer.write(
                (message + "\n").encode("utf-8")
            )
            await writer.drain()

    except websockets.exceptions.ConnectionClosed:
        pass

    except Exception as error:
        print(
            f"[WEB ERROR] {username}: {error}"
        )

    finally:
        if reader_task:
            reader_task.cancel()

        if writer:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

        if websocket in connected_clients:
            del connected_clients[websocket]

        if username:
            print(f"[CLEANUP] {username}")

        await broadcast_users()


async def main():
    print()
    print("=" * 52)
    print("             WEB <-> TCP CHAT BRIDGE")
    print("=" * 52)
    print(f"WebSocket: ws://127.0.0.1:{WEBSOCKET_PORT}")
    print(f"TCP Chat:  {TCP_HOST}:{TCP_PORT}")
    print("=" * 52)
    print("Username-only login")
    print("Waiting for browser clients...")
    print()

    async with websockets.serve(
        handle_browser,
        WEBSOCKET_HOST,
        WEBSOCKET_PORT
    ):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWeb backend stopped.")
