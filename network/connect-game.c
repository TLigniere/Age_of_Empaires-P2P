#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <conio.h> 
#include <time.h>

#pragma comment(lib, "ws2_32.lib")

#define BUFFER_SIZE 4096
#define TICK_RATE_MS 100
#define QUEUE_MAX 10
#define MSG_LEN 64

// --- GESTION DE LA FILE (FIFO) ---
typedef struct {
    char items[QUEUE_MAX][MSG_LEN];
    int front; // Indice du premier élément (le plus ancien)
    int rear;  // Indice du dernier élément (le plus récent)
    int count; // Nombre d'éléments actuels
} Queue;

void initQueue(Queue *q) {
    q->front = 0;
    q->rear = -1;
    q->count = 0;
}

int isFull(Queue *q) {
    return q->count == QUEUE_MAX;
}

int isEmpty(Queue *q) {
    return q->count == 0;
}

void enqueue(Queue *q, char *msg) {
    if (isFull(q)) {
        printf("\n[!] File pleine ! Impossible d'ajouter : %s\n", msg);
    } else {
        // Calcul circulaire pour revenir à 0 si on dépasse QUEUE_MAX
        q->rear = (q->rear + 1) % QUEUE_MAX;
        
        strcpy(q->items[q->rear], msg);
        q->count++;
        
        printf("\n[QUEUE] Ajout (Enqueue) : %s\n", msg);
    }
}

void dequeue(Queue *q) {
    if (isEmpty(q)) {
        printf("\n[!] File vide ! Rien a traiter.\n");
    } else {
        // On récupère l'élément à la tête (front)
        printf("\n[QUEUE] Traitement (Dequeue - Plus Ancien) : %s\n", q->items[q->front]);
        
        // On avance la tête
        q->front = (q->front + 1) % QUEUE_MAX;
        q->count--;
    }
}

void printQueue(Queue *q) {
    if (isEmpty(q)) {
        printf("\n--- FILE VIDE ---\n");
    } else {
        printf("\n--- CONTENU FILE ---\n");
        
        int i = 0;
        int current_idx = q->front;
        
        while (i < q->count) {
            printf("[%d] -> %s", i, q->items[current_idx]);
            printf("\n");
            
            current_idx = (current_idx + 1) % QUEUE_MAX;
            i++;
        }
    }
}

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

    srand(time(NULL));
    init_winsock();
    int my_port = atoi(argv[1]);
    int dest_port = atoi(argv[2]);

    SOCKET sock = socket(AF_INET, SOCK_DGRAM, 0);
    
    // Config réception
    struct sockaddr_in my_addr;
    my_addr.sin_family = AF_INET;
    my_addr.sin_addr.s_addr = INADDR_ANY;
    my_addr.sin_port = htons(my_port);
    bind(sock, (struct sockaddr*)&my_addr, sizeof(my_addr));

    // Config envoi
    struct sockaddr_in dest_addr;
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    dest_addr.sin_port = htons(dest_port);

    // Initialisation de la FILE (Queue)
    Queue dataQueue;
    initQueue(&dataQueue);

    printf("=== SYSTEME FILE D'ATTENTE (FIFO) ===\n");
    printf(" [m] Envoyer un message manuel (VAR:x)\n");
    printf(" [v] Voir la file (View)\n");
    printf(" [d] Depiler le plus ANCIEN (Dequeue)\n");
    printf(" [q] Quitter\n\n");

    fd_set readfds;
    struct timeval timeout;

    while (1) {
        
        // RECEPTION
        FD_ZERO(&readfds);
        FD_SET(sock, &readfds);
        
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
                
                char extracted_val[MSG_LEN];
                
                if (strncmp(recv_buffer, "VAR:", 4) == 0) {
                    strcpy(extracted_val, recv_buffer + 4);
                    printf("\n [RECU] Variable : '%s'", extracted_val);
                    
                    // AJOUT DANS LA FILE (Enqueue)
                    enqueue(&dataQueue, extracted_val);
                } else {
                    printf("\n [RECU] Ignore : %s\n", recv_buffer);
                }
            }
        }

        // INPUT CLAVIER
        if (_kbhit()) {
            char c = _getch();
            
            if (c == 'q') break;

            if (c == 'm') {
                char msg[64];
                int random_val = rand() % 100;
                sprintf(msg, "VAR:Action_%d", random_val);
                
                sendto(sock, msg, strlen(msg), 0, (struct sockaddr*)&dest_addr, sizeof(dest_addr));
                printf("\n>>> [MANUAL SENT] %s\n", msg);
            }

            if (c == 'v') {
                printQueue(&dataQueue);
            }

            if (c == 'd') {
                dequeue(&dataQueue);
            }
        }
    }

    closesocket(sock);
    WSACleanup();
    return 0;
}