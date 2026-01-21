#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <conio.h> // Pour _kbhit()

#pragma comment(lib, "ws2_32.lib")

#define BUFFER_SIZE 4096

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

    // 1. Création de la Socket UDP (SOCK_DGRAM)
    SOCKET sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock == INVALID_SOCKET) {
        printf("Erreur creation socket\n");
        return 1;
    }

    // 2. Préparation de MON adresse (pour recevoir)
    struct sockaddr_in my_addr;
    my_addr.sin_family = AF_INET;
    my_addr.sin_addr.s_addr = INADDR_ANY; // J'accepte les paquets sur toutes mes interfaces
    my_addr.sin_port = htons(my_port);

    // 3. Binding (INDISPENSABLE en UDP pour recevoir)
    if (bind(sock, (struct sockaddr*)&my_addr, sizeof(my_addr)) == SOCKET_ERROR) {
        printf("Erreur Bind sur le port %d (Code: %d)\n", my_port, WSAGetLastError());
        return 1;
    }

    // 4. Préparation de l'adresse du DESTINATAIRE (pour envoyer)
    struct sockaddr_in dest_addr;
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_addr.s_addr = inet_addr("127.0.0.1"); // Localhost pour le test
    dest_addr.sin_port = htons(dest_port);

    printf("=== CHAT UDP P2P ===\n");
    printf("Je suis sur le port : %d\n", my_port);
    printf("J'envoie vers     : %d\n", dest_port);
    printf("Ecrivez et validez par Entree...\n\n");

    // --- Variables pour la boucle ---
    char send_buffer[BUFFER_SIZE] = {0};
    int send_pos = 0;
    
    fd_set readfds;
    struct timeval timeout;

    // --- BOUCLE PRINCIPALE (Game Loop style) ---
    while (1) {
        // A. Surveillance Réseau (Polling)
        FD_ZERO(&readfds);
        FD_SET(sock, &readfds);

        timeout.tv_sec = 0;
        timeout.tv_usec = 10000; // 10ms

        int activity = select(0, &readfds, NULL, NULL, &timeout);

        // B. Si on a reçu un paquet UDP
        if (activity > 0 && FD_ISSET(sock, &readfds)) {
            char recv_buffer[BUFFER_SIZE];
            struct sockaddr_in sender_addr;
            int sender_len = sizeof(sender_addr);

            // recvfrom nous donne aussi l'adresse de qui a envoyé (sender_addr)
            int valread = recvfrom(sock, recv_buffer, BUFFER_SIZE - 1, 0, (struct sockaddr*)&sender_addr, &sender_len);

            if (valread > 0) {
                recv_buffer[valread] = '\0';
                // Affichage propre (on efface la ligne de saisie en cours)
                printf("\r[Recept] %s\n> %s", recv_buffer, send_buffer);
            }
        }

        // C. Si on tape au clavier (Polling local)
        if (_kbhit()) {
            char c = _getch();
            if (c == '\r' || c == '\n') { // Touche Entrée
                send_buffer[send_pos] = '\0';
                printf("\n");

                // ENVOI UDP (sendto)
                // Pas de connexion préalable, on donne l'adresse à chaque envoi
                int sent = sendto(sock, send_buffer, strlen(send_buffer), 0, (struct sockaddr*)&dest_addr, sizeof(dest_addr));
                
                if (sent == SOCKET_ERROR) {
                    printf("[Erreur Envoi] Code: %d\n", WSAGetLastError());
                }

                // Reset buffer
                send_pos = 0;
                memset(send_buffer, 0, BUFFER_SIZE);
                printf("> ");

            } else if (c == '\b' && send_pos > 0) { // Backspace
                printf("\b \b");
                send_pos--;
            } else if (send_pos < BUFFER_SIZE - 1 && c >= 32 && c <= 126) {
                printf("%c", c);
                send_buffer[send_pos++] = c;
            }
        }
    }

    closesocket(sock);
    WSACleanup();
    return 0;
}