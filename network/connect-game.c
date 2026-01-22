#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <conio.h> 

#pragma comment(lib, "ws2_32.lib")

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
    if (argc < 3) {
        printf("Usage: %s <MON_PORT> <PORT_DEST>\n", argv[0]);
        return 1;
    }

    init_winsock();
    int my_port = atoi(argv[1]);
    int dest_port = atoi(argv[2]);

    SOCKET sock = socket(AF_INET, SOCK_DGRAM, 0);
    
    // Config pour réception
    struct sockaddr_in my_addr;
    my_addr.sin_family = AF_INET;
    my_addr.sin_addr.s_addr = INADDR_ANY;
    my_addr.sin_port = htons(my_port);
    bind(sock, (struct sockaddr*)&my_addr, sizeof(my_addr));

    // Config pour envoi
    struct sockaddr_in dest_addr;
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    dest_addr.sin_port = htons(dest_port);

    printf("[INFO] Appuyez sur 's' pour lancer/arreter l'envoi auto.\n");
    printf("[INFO] Appuyez sur 'q' pour quitter.\n\n");

    fd_set readfds;
    struct timeval timeout;

    int auto_mode = 0;          // 0 = manuel, 1 = automatique
    DWORD last_tick = 0;        // Mesure de temps
    long packet_id = 0;         // Compteur de paquets

    while (1) {
        if (auto_mode && (GetTickCount() - last_tick >= TICK_RATE_MS)) {
            char auto_msg[64];
            
            sprintf(auto_msg, "packet : %ld", packet_id);
            
            sendto(sock, auto_msg, strlen(auto_msg), 0, (struct sockaddr*)&dest_addr, sizeof(dest_addr));
            
            printf("\r[SPAM LOOP] %s   ", auto_msg);
            
            packet_id++;
            last_tick = GetTickCount(); // Reset du chrono
        }

        // 2. RECEPTION RESEAU (Non bloquant via Select)
        FD_ZERO(&readfds);
        FD_SET(sock, &readfds);
        
        // Timeout très court (10ms) pour que la boucle tourne vite
        timeout.tv_sec = 0;
        timeout.tv_usec = 10000; 

        int activity = select(0, &readfds, NULL, NULL, &timeout);

        if (activity > 0 && FD_ISSET(sock, &readfds)) {
            char recv_buffer[BUFFER_SIZE];
            struct sockaddr_in sender;
            int len = sizeof(sender);
            int valread = recvfrom(sock, recv_buffer, BUFFER_SIZE - 1, 0, (struct sockaddr*)&sender, &len);
            
            if (valread > 0) {
                recv_buffer[valread] = '\0';
                // On affiche ce qu'on reçoit (venant de l'autre jeu)
                printf("\n [RECEPT]-> %s\n", recv_buffer);
            }
        }

        // INPUT CLAVIER
        if (_kbhit()) {
            char c = _getch();
            if (c == 'q') {
                break;
            } else
            
            if (c == 's') {
                auto_mode = !auto_mode;
            }
        }
    }

    closesocket(sock);
    WSACleanup();
    return 0;
}