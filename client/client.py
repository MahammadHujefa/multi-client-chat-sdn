import socket
import threading

SERVER_IP = "10.0.0.3"
PORT = 5000
BUFFER_SIZE = 1024


def receive_messages(client_socket):
    while True:
        try:
            data = client_socket.recv(BUFFER_SIZE)

            if not data:
                print("\nDisconnected from server.")
                break

            print(data.decode("utf-8"), end="")

        except:
            break


def send_messages(client_socket):
    while True:
        try:
            message = input()

            if message.lower() == "/quit":
                break

            client_socket.send(
                message.encode("utf-8")
            )

        except:
            break


def main():

    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    print("Connecting to server...")

    client_socket.connect(
        (SERVER_IP, PORT)
    )

    print("Connected to server!")

    # Receive username request
    data = client_socket.recv(BUFFER_SIZE)

    print(data.decode("utf-8"), end="")

    # Enter username
    username = input()

    client_socket.send(
        username.encode("utf-8")
    )

    # Start receiving thread
    receive_thread = threading.Thread(
        target=receive_messages,
        args=(client_socket,)
    )

    receive_thread.daemon = True
    receive_thread.start()

    # Send messages
    send_messages(client_socket)

    client_socket.close()

    print("Client closed.")


if __name__ == "__main__":
    main()
