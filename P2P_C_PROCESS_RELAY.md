# P2P Through C Process - Updated Documentation

## Architecture

The P2P system now uses the **C process as a relay server** for all event communication:

```
Player 1 (J1)           C Process           Player 2 (J2)
    │                      │                      │
    ├─ Logs events         │                      │
    ├─ Sends via→──────→───┤                      │
    │   NetworkClient       │                      │
    │                       ├─ Relays events ────→ Receives
    │                       │                      │
    │              ←────────┼──── Relays from J2 ──┤
    ├─ Receives    ←────────┤   (J2's events)      │
    │                       │                      │
    └─ Displays on          │                      │
       terminal             │                      │
```

## How It Works

### Event Flow (Example: J1 moves unit)

1. **Player 1 performs action** → Unit movement
2. **EventLogger logs** → `UNIT_MOVE` event with timestamp
3. **Send to C process** → Uses `NetworkClient.send()`
4. **C process receives** → Via port 5000 (or configured)
5. **C process forwards** → Sends to Player 2
6. **Player 2 receives** → Via port 5001 (or configured)
7. **Consume events** → `p2p_network.consume_events()`
8. **Display on terminal** → `[J1] UNIT_MOVE: {...}`

## Setup Requirements

### 1. Enable C Process Support
You need to have the C process (GameP2P.exe) running or compiled.

### 2. Configure ENABLE_NETWORK and ENABLE_P2P

In the configuration section or via environment:

```python
ENABLE_NETWORK = True   # Required for C process communication
ENABLE_P2P = True       # Enable P2P relay through C
```

### 3. Port Configuration

The system uses these ports:
- **Port 5000**: J1 listens here / C sends to
- **Port 5001**: J2 listens here / C sends to
- **Port 6000**: Destination (where C relay goes)

Can be modified via command line:
```bash
python controller.py --p2p --player J1 --my-port 5000
```

## Usage

### Start C Process First

Ensure the C process is running:
```bash
./GameP2P.exe <my_port> <opponent_port> <python_port>
```

### Terminal 1 - Player 1
```bash
# Enable C process relay
python controller.py --p2p --player J1 --my-port 5000 graphics
```

### Terminal 2 - Player 2
```bash
python controller.py --p2p --player J2 --my-port 5001 graphics
```

## Event Types

| Type | From | To | Via C |
|------|------|-----|---------|
| UNIT_MOVE | Player | C | ✓ |
| BUILDING_CONSTRUCT | Player | C | ✓ |
| UNIT_CREATE | Player | C | ✓ |
| RESOURCE_GATHER | Player | C | ✓ |
| ATTACK | Player | C | ✓ |

## Message Format (Via C Process)

Events are sent to C as JSON:

```json
{
  "type": "UNIT_MOVE",
  "player": "J1",
  "timestamp": "2026-01-27T15:30:45.123456",
  "data": {"unit_id": 12345, "x": 15, "y": 20}
}
```

### How C Receives It

```python
network_client.send("UNIT_MOVE", json_string)
```

### C Process Relays To

Player 2's listening port (5001) receives:
```
MESSAGE: UNIT_MOVE|{JSON_DATA}
```

## Code Changes

### P2PNetworkClient Now Takes NetworkClient

**Before:**
```python
p2p_network = P2PNetworkClient(my_port=5000, opponent_port=5001)
```

**After:**
```python
network = NetworkClient(...)  # Connect to C process
p2p_network = P2PNetworkClient(network_client=network, player_side='J1')
```

### Event Sending Through C

```python
def send_event(self, event):
    """Send through C process"""
    msg = json.dumps(event)
    self.network_client.send(event_type, msg)  # Via C process
```

### Event Receiving From C

```python
def poll(self):
    """Poll C process for events"""
    self.network_client.poll()  # Check C process
    messages = self.network_client.consume_messages()
    # Filter for opponent events
    for msg_type, payload in messages:
        if msg_type in ['UNIT_MOVE', 'BUILDING_CONSTRUCT', ...]:
            # Parse and add to inbox
```

## Advantages of C Process Relay

✅ **Centralized relay point** - Single server managing all events  
✅ **Event validation** - C can validate events before forwarding  
✅ **Load balancing** - C can handle multiple players  
✅ **Network security** - C acts as firewall/proxy  
✅ **Logging capability** - All events can be logged by C  
✅ **Scalability** - Easy to add more players (3v3, 4v4, etc.)

## Troubleshooting

### "C process not connected" Error

```
[P2P] Erreur: C process non connecté. Activez ENABLE_NETWORK
```

**Solution:**
- Ensure C process is running
- Check `ENABLE_NETWORK` is True
- Verify port configuration matches

### Events Not Appearing

1. Verify C process is receiving events:
   - Check C process console for messages
   - Verify JSON format is correct

2. Verify C process is forwarding:
   - Check opponent instance is running
   - Verify ports match configuration

3. Check network connectivity:
   ```bash
   netstat -an | grep 5000  # Check if port is listening
   ```

### Connection Timeout

```
[P2P] ⚠️  Connexion perdue
```

- C process crashed/disconnected
- Network interrupted
- Firewall blocking ports

## Configuration File

You can also configure via `config.ini` (when implemented):

```ini
[P2P]
enable_p2p = true
enable_network = true
player_side = J1
my_port = 5000
opponent_port = 5001
opponent_host = 127.0.0.1
```

## Security Notes

When using C process relay:
- **Message signing**: Consider adding message signatures
- **Event validation**: C should validate event legality
- **Rate limiting**: Prevent event spam
- **Encryption**: Use TLS for remote networks

## Future Enhancements

1. **Event Queuing** - C process queues events until delivered
2. **Acknowledgment** - J2 confirms receipt to J1 via C
3. **State Sync** - Periodic full state verification through C
4. **Spectator Mode** - Third player watches via C
5. **Replay System** - C records all events for replay

## Testing the C Relay

```bash
# Terminal 1: Start J1
python controller.py --p2p --player J1 --my-port 5000 graphics

# Terminal 2: Start J2
python controller.py --p2p --player J2 --my-port 5001 graphics

# In-game: Move units, construct buildings
# Expected: See events from opponent in console
```

## C Process Requirements

The C process must:
1. Listen on configured port
2. Accept JSON messages
3. Parse event type
4. Route to correct opponent port
5. Forward complete event data

See `connect-game.c` in network folder for implementation details.
