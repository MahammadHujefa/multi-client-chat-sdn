import socket
import threading
import time
import statistics
import sys

SERVER_HOST ="10.0.0.4"
SERVER_PORT = 5000
CLIENTS = 5
TIMEOUT = 5

results = []
errors = []
lock = threading.Lock()


def test_client(number):
    username = f"perfuser{number}"
    client = None

    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(TIMEOUT)
        client.connect((SERVER_HOST, SERVER_PORT))

        # Register the test user.
        client.sendall((username + "\n").encode())

        # Read the server's response.
        response = client.recv(4096)

        if not response:
            raise RuntimeError("Server closed the connection")

        # Measure a request and response.
        start = time.perf_counter()
        client.sendall(b"/help\n")
        response = client.recv(4096)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if not response:
            raise RuntimeError("No response received for /help")

        with lock:
            results.append(elapsed_ms)

        print(
            f"Client {number}: SUCCESS | "
            f"Response time: {elapsed_ms:.2f} ms"
        )

    except Exception as error:
        with lock:
            errors.append(f"Client {number}: {error}")
        print(f"Client {number}: FAILED | {error}")

    finally:
        if client:
            try:
                client.sendall(b"/quit\n")
                client.close()
            except OSError:
                pass


def main():
    print("TCP Chat Server Performance Test")
    print(f"Target: {SERVER_HOST}:{SERVER_PORT}")
    print(f"Simultaneous clients: {CLIENTS}")
    print("-" * 45)

    threads = []

    for number in range(1, CLIENTS + 1):
        thread = threading.Thread(target=test_client, args=(number,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("\n========== RESULTS ==========")
    print(f"Total clients: {CLIENTS}")
    print(f"Successful clients: {len(results)}")
    print(f"Failed clients: {len(errors)}")

    if results:
        print(f"Average response time: {statistics.mean(results):.2f} ms")
        print(f"Minimum response time: {min(results):.2f} ms")
        print(f"Maximum response time: {max(results):.2f} ms")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(error)

    print("=============================")


if __name__ == "__main__":
    main()
