// connect-game.c
// Compilation : gcc connect-game.c -o GameP2P.exe -lws2_32

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <process.h>

#define BUFFER_SIZE 4096

SOCKET sock;
struct sockaddr_in dest_addr;

unsigned __stdcall ThreadEnvoi(void *arg) {
    char buffer[BUFFER_SIZE];
    
    while (fgets(buffer, BUFFER_SIZE, stdin) != NULL) {
        
        buffer[strcspn(buffer, "\r\n")] = 0;

        if (strlen(buffer) > 0) {
            // Envoi UDP
            sendto(sock, buffer, strlen(buffer), 0, (struct sockaddr*)&dest_addr, sizeof(dest_addr));
            
            // fprintf(stderr, "[C-BRIDGE] Sent: %s\n", buffer);
        }
    }
    return 0;
}

void init_winsock() {
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        exit(1);
    }
}

int main(int argc, char *argv[]) {
    setvbuf(stdout, NULL, _IONBF, 0);

    if (argc < 3) {
        fprintf(stderr, "Usage: %s <MON_PORT> <PORT_DEST>\n", argv[0]);
        return 1;
    }

    init_winsock();
    int my_port = atoi(argv[1]);
    int dest_port = atoi(argv[2]);

    sock = socket(AF_INET, SOCK_DGRAM, 0);

    // Reception
    struct sockaddr_in my_addr;
    my_addr.sin_family = AF_INET; 
    my_addr.sin_addr.s_addr = INADDR_ANY; 
    my_addr.sin_port = htons(my_port);
    bind(sock, (struct sockaddr*)&my_addr, sizeof(my_addr));

    // Envoi
    dest_addr.sin_family = AF_INET; 
    dest_addr.sin_addr.s_addr = inet_addr("127.0.0.1"); 
    dest_addr.sin_port = htons(dest_port);

    // Lancement thread ecoute pyhton
    _beginthreadex(NULL, 0, &ThreadEnvoi, NULL, 0, NULL);

    fprintf(stderr, "=== PONT C PRET (Port %d -> %d) ===\n", my_port, dest_port);

    // Ecoute reseau -> python
    char recv_buffer[BUFFER_SIZE];
    struct sockaddr_in sender; 
    int len = sizeof(sender);

    while (1) {
        int valread = recvfrom(sock, recv_buffer, BUFFER_SIZE - 1, 0, (struct sockaddr*)&sender, &len);
        
        if (valread > 0) {
            recv_buffer[valread] = '\0';
            
            printf("%s\n", recv_buffer);
        }
    }

    closesocket(sock);
    WSACleanup();
    return 0;
}