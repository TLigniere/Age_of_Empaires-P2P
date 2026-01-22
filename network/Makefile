CC = gcc
CFLAGS = -Wall -g
LDFLAGS = -lws2_32

TARGET = GameP2P.exe

OBJS = connect-game.o fifo.o

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) -o $(TARGET) $(OBJS) $(LDFLAGS)

connect-game.o: connect-game.c fifo.h
	$(CC) $(CFLAGS) -c connect-game.c

fifo.o: fifo.c fifo.h
	$(CC) $(CFLAGS) -c fifo.c

clean:
	del *.o $(TARGET)