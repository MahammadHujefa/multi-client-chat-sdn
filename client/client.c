#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 5000
#define BUFFER_SIZE 1024

int main()
{
    int client_socket;

    struct sockaddr_in server_addr;

    char buffer[BUFFER_SIZE];

    // 1. Create TCP socket
    client_socket = socket(AF_INET, SOCK_STREAM, 0);

    if (client_socket < 0)
    {
        perror("Socket creation failed");
        return 1;
    }

    printf("Client socket created successfully.\n");

    // 2. Configure server address
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(PORT);
    server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");

    // 3. Connect to server
    if (connect(client_socket,
                (struct sockaddr *)&server_addr,
                sizeof(server_addr)) < 0)
    {
        perror("Connection failed");
        close(client_socket);
        return 1;
    }

    printf("Connected to server!\n");

    // 4. Send message
    char message[] = "Hello from Client!";

    send(
        client_socket,
        message,
        strlen(message),
        0
    );

    printf("Message sent to server.\n");

    // 5. Receive reply
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

        printf("Server says: %s\n", buffer);
    }

    // 6. Close socket
    close(client_socket);

    printf("Client closed.\n");

    return 0;
}
