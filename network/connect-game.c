//connect-game.c v0.2.1
//Compilation : gcc connect-game.c -o GameP2P.exe -lws2_32

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>

#pragma comment(lib, "ws2_32.lib")
#define BUFFER_SIZE 4096

int main(int argc, char *argv[]) {
    if (argc < 4) {
        printf("Usage: %s <MY_PORT> <DEST_PORT> <PY_PORT>\n", argv[0]);
        return 1;
    }

    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return 1;

    int my_port = atoi(argv[1]);
    int dest_port = atoi(argv[2]);
    int py_port = atoi(argv[3]);

    SOCKET sock = socket(AF_INET, SOCK_DGRAM, 0);

    // conf socket reception
    struct sockaddr_in me;
    me.sin_family = AF_INET;
    me.sin_addr.s_addr = INADDR_ANY; 
    me.sin_port = htons(my_port);
    
    if (bind(sock, (struct sockaddr*)&me, sizeof(me)) < 0) {
        printf("! Erreur Bind port %d. (Deja lance ?)\n", my_port);
        return 1;
    }
    
    // conf socket envoi externe
    struct sockaddr_in dest_addr;
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    dest_addr.sin_port = htons(dest_port);

    // conf socket envoi python
    struct sockaddr_in py_addr;
    py_addr.sin_family = AF_INET;
    py_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    py_addr.sin_port = htons(py_port);
    printf("Ecoute sur le port : %d\n", my_port);
    printf("Python local est sur : %d\n", py_port);
    printf("Adversaire est sur : %d\n", dest_port);

    char buffer[BUFFER_SIZE];
    struct sockaddr_in sender;
    int len = sizeof(sender);

    while (1) {
        int n = recvfrom(sock, buffer, BUFFER_SIZE, 0, (struct sockaddr*)&sender, &len);
        
        if (n > 0) {
            
            // test si vient python
            if (sender.sin_addr.s_addr == inet_addr("127.0.0.1") && sender.sin_port == htons(py_port)) {
                
                sendto(sock, buffer, n, 0, (struct sockaddr*)&dest_addr, sizeof(dest_addr));
                
            } 
            else {
                sendto(sock, buffer, n, 0, (struct sockaddr*)&py_addr, sizeof(py_addr));
            }
        }
    }

    closesocket(sock);
    WSACleanup();
    return 0;
}