#include <winsock2.h>
#include <ws2tcpip.h>
#include <stdio.h>

#pragma comment(lib, "ws2_32.lib")

#define BUF_SIZE 1024

int main() {
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2,2), &wsaData);

    char *my_state = "{\"position\": [1,2], \"health\": 100}";
    char *peer_ip = "127.0.0.1";
    int my_port = 5000;
    int peer_port = 5001;

    //Créer socket serveur
    SOCKET listen_sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in my_addr;
    my_addr.sin_family = AF_INET;
    my_addr.sin_addr.s_addr = INADDR_ANY;
    my_addr.sin_port = htons(my_port);
    bind(listen_sock, (struct sockaddr*)&my_addr, sizeof(my_addr));
    listen(listen_sock, 1);

    printf("Peer en écoute sur port %d...\n", my_port);

    //Se connecter au peer et envoyer état
    SOCKET send_sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in peer_addr;
    peer_addr.sin_family = AF_INET;
    peer_addr.sin_port = htons(peer_port);
    inet_pton(AF_INET, peer_ip, &peer_addr.sin_addr);

    Sleep(1000); // attendre que l'autre peer écoute
    if (connect(send_sock, (struct sockaddr*)&peer_addr, sizeof(peer_addr)) == 0) {
        send(send_sock, my_state, (int)strlen(my_state), 0);
        printf("Etat envoyé à %s:%d\n", peer_ip, peer_port);
    } else {
        printf("Impossible de se connecter au peer.\n");
    }
    closesocket(send_sock);

    //Accepter la connexion du peer et recevoir son état
    SOCKET client_sock = accept(listen_sock, NULL, NULL);
    char buffer[BUF_SIZE] = {0};
    int n = recv(client_sock, buffer, BUF_SIZE, 0);
    if (n > 0) {
        printf("Etat reçu : %s\n", buffer);
    }

    closesocket(client_sock);
    closesocket(listen_sock);
    WSACleanup();
    return 0;
}
