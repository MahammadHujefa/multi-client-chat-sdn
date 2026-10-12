#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 5000
#define BUFFER_SIZE 1024

int main()
{
    int server_socket;
    int client_socket;

    struct sockaddr_in server_addr;
    struct sockaddr_in client_addr;

    socklen_t client_len = sizeof(client_addr);

    char buffer[BUFFER_SIZE];

    // 1. Create TCP socket
    server_socket = socket(AF_INET, SOCK_STREAM, 0);

    if (server_socket < 0)
    {
        perror("Socket creation failed");
        return 1;
    }

    printf("Socket created successfully.\n");

    // 2. Configure server address
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT);

    // 3. Bind socket to IP and port
    if (bind(server_socket,
             (struct sockaddr *)&server_addr,
             sizeof(server_addr)) < 0)
    {
        perror("Bind failed");
        close(server_socket);
        return 1;
    }

    printf("Socket bound to port %d.\n", PORT);

    // 4. Listen for clients
    if (listen(server_socket, 5) < 0)
    {
        perror("Listen failed");
        close(server_socket);
        return 1;
    }

    printf("Server is listening...\n");
    printf("Waiting for a client...\n");

    // 5. Accept a client
    client_socket = accept(
        server_socket,
        (struct sockaddr *)&client_addr,
        &client_len
    );

    if (client_socket < 0)
    {
        perror("Accept failed");
        close(server_socket);
        return 1;
    }

    printf("Client connected!\n");

    // 6. Receive message from client
    memset(buffer, 0, BUFFER_SIZE);

    int bytes_received = recv(
        client_socket,
        buffer,
        BUFFER_SIZE - 1,
        0
    );

    if (bytes_received > 0)
    {
        buffer[bytes_received] = '\0';

        printf("Client says: %s\n", buffer);
    }

    // 7. Send reply
    char reply[] = "Hello from TCP Server!";

    send(
        client_socket,
        reply,
        strlen(reply),
        0
    );

    printf("Reply sent to client.\n");

    // 8. Close connections
    close(client_socket);
    close(server_socket);

    printf("Server closed.\n");

    return 0;
}
