// fifo.c
#include <stdio.h>
#include <string.h>
#include "fifo.h"

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
        q->rear = (q->rear + 1) % QUEUE_MAX;
        strcpy(q->items[q->rear], msg);
        q->count++;
        printf("\n[QUEUE] Ajout : %s\n", msg);
    }
}

void dequeue(Queue *q) {
    if (isEmpty(q)) {
        printf("\n[!] File vide ! Rien a traiter.\n");
    } else {
        printf("\n[QUEUE] Traitement : %s\n", q->items[q->front]);
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