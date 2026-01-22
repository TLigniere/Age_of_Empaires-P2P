// connect-game.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <conio.h> 
#include <time.h>

#include "fifo.h"

// #pragma comment(lib, "ws2_32.lib")

#define BUFFER_SIZE 4096
#define TICK_RATE_MS 100

void init_winsock() {
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        printf("Erreur WSAStartup\n");
        exit(1);
    }
}

int main(int argc, char *argv[]) {
    if (argc < 3) { printf("Usage: %s <MON_PORT> <PORT_DEST>\n", argv[0]); return 1; }
    
    srand(time(NULL));
    init_winsock();
    int my_port = atoi(argv[1]);
    int dest_port = atoi(argv[2]);

    SOCKET sock = socket(AF_INET, SOCK_DGRAM, 0);
    struct sockaddr_in my_addr;
    my_addr.sin_family = AF_INET; my_addr.sin_addr.s_addr = INADDR_ANY; my_addr.sin_port = htons(my_port);
    bind(sock, (struct sockaddr*)&my_addr, sizeof(my_addr));

    struct sockaddr_in dest_addr;
    dest_addr.sin_family = AF_INET; dest_addr.sin_addr.s_addr = inet_addr("127.0.0.1"); dest_addr.sin_port = htons(dest_port);

    Queue dataQueue;
    initQueue(&dataQueue);
    
    fd_set readfds;
    struct timeval timeout;

    printf("=== SYSTEME FILE D'ATTENTE (FIFO) ===\n");
    printf(" [m] Envoyer un message manuel (VAR:x)\n");
    printf(" [v] Voir la file (View)\n");
    printf(" [d] Depiler le plus ANCIEN \n");
    printf(" [q] Quitter\n\n");

    while (1) {
        FD_ZERO(&readfds); FD_SET(sock, &readfds);
        timeout.tv_sec = 0; timeout.tv_usec = 10000; 

        if (select(0, &readfds, NULL, NULL, &timeout) > 0 && FD_ISSET(sock, &readfds)) {
            char recv_buffer[BUFFER_SIZE];
            struct sockaddr_in sender; int len = sizeof(sender);
            int valread = recvfrom(sock, recv_buffer, BUFFER_SIZE - 1, 0, (struct sockaddr*)&sender, &len);
            
            if (valread > 0) {
                recv_buffer[valread] = '\0';
                if (strncmp(recv_buffer, "VAR:", 4) == 0) {
                    char extracted_val[MSG_LEN];
                    strcpy(extracted_val, recv_buffer + 4);
                    printf("\n [RECU] Variable : '%s'", extracted_val);
                    
                    enqueue(&dataQueue, extracted_val);
                }
            }
        }

        if (_kbhit()) {
            char c = _getch();
            if (c == 'q') break;
            
            if (c == 'm') {
                char msg[64];
                sprintf(msg, "VAR:Action_%d", rand() % 100);
                sendto(sock, msg, strlen(msg), 0, (struct sockaddr*)&dest_addr, sizeof(dest_addr));
                printf("\n>>> SENT %s\n", msg);
            }
            if (c == 'v') printQueue(&dataQueue);
            if (c == 'd') dequeue(&dataQueue);
        }
    }
    closesocket(sock);
    WSACleanup();
    return 0;
}