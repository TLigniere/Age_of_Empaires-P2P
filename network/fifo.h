// fifo.h
#ifndef FIFO_H
#define FIFO_H

#define QUEUE_MAX 10
#define MSG_LEN 64

// Définition de la structure
typedef struct {
    char items[QUEUE_MAX][MSG_LEN];
    int front;
    int rear;
    int count;
} Queue;

// Prototypes des fonctions
void initQueue(Queue *q);
int isFull(Queue *q);
int isEmpty(Queue *q);
void enqueue(Queue *q, char *msg);
void dequeue(Queue *q);
void printQueue(Queue *q);

#endif