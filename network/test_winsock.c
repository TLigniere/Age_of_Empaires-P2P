#include <stdio.h>
#include <winsock2.h> // Header obligatoire pour les sockets sous Windows

// Ligne optionnelle pour certains compilateurs (MSVC), 
// mais généralement on gère cela via la commande de compilation sous MinGW/GCC.
#pragma comment(lib,"ws2_32.lib") 

int main() {
    WSADATA wsaData;
    int iResult;

    // 1. Initialisation de Winsock
    // MAKEWORD(2,2) demande la version 2.2 de Winsock
    printf("Tentative d'initialisation de Winsock...\n");
    
    iResult = WSAStartup(MAKEWORD(2, 2), &wsaData);
    
    if (iResult != 0) {
        printf("Echec de WSAStartup : %d\n", iResult);
        return 1;
    }
    
    printf("Succes ! Winsock est initialise.\n");
    printf("Status du systeme : %s\n", wsaData.szSystemStatus);

    // 2. Nettoyage (Appel système pour libérer les ressources)
    WSACleanup();
    printf("Nettoyage effectue. Votre environnement est pret.\n");

    return 0;
}