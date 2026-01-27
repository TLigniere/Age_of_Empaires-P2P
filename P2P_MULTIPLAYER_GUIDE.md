# P2P Multiplayer Guide

## Overview
The game now supports P2P (Peer-to-Peer) multiplayer mode where two players can connect and play simultaneously on different ports, with game events synchronized between them.

## Quick Start

### Prerequisites
- Two terminal windows or two machines on the same network
- Python 3.7+
- Both instances need to have the game files

### Running P2P Mode

#### Player 1 (J1) - Graphics Mode
```bash
python controller.py --p2p --player J1 --my-port 5000 --opponent-port 5001 graphics
```

#### Player 2 (J2) - Graphics Mode  
```bash
python controller.py --p2p --player J2 --my-port 5001 --opponent-port 5000 graphics
```

#### Player 1 (J1) - Terminal Mode
```bash
python controller.py --p2p --player J1 --my-port 5000 --opponent-port 5001
```

#### Player 2 (J2) - Terminal Mode
```bash
python controller.py --p2p --player J2 --my-port 5001 --opponent-port 5000
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--p2p` | Enable P2P multiplayer mode | Disabled |
| `--player J1\|J2` | Set player side | J1 |
| `--my-port PORT` | Local listening port | 5000 for J1, 5001 for J2 |
| `--opponent-port PORT` | Opponent's port | 5001 for J1, 5000 for J2 |
| `--opponent-host HOST` | Opponent's host/IP | 127.0.0.1 (localhost) |
| `graphics` | Use graphics mode (optional) | Terminal mode |

## Network Communication

### Event Types
The system automatically logs and syncs these events:
- `UNIT_MOVE` - Unit movement
- `BUILDING_CONSTRUCT` - Building construction
- `UNIT_CREATE` - Unit creation  
- `RESOURCE_GATHER` - Resource gathering
- `ATTACK` - Combat attacks

### Message Format
Events are sent as JSON objects:
```json
{
  "type": "UNIT_MOVE",
  "player": "J1",
  "timestamp": "2026-01-27T15:30:45.123456",
  "data": {"unit_id": 12345, "x": 15, "y": 20}
}
```

### Network Architecture
- **Protocol**: UDP (connectionless, fast)
- **Encoding**: JSON for events
- **Port Configuration**: Customizable per instance
- **Local Network**: Currently works on localhost or local network

## Remote Network Setup

To play across the internet, use SSH port forwarding:

### Machine 1 (J1 player)
```bash
# Forward port 5001 from opponent machine to local 5001
ssh -L 5001:localhost:5001 user@opponent-ip
# Then run:
python controller.py --p2p --player J1 --my-port 5000 --opponent-port 5001 --opponent-host localhost
```

### Machine 2 (J2 player)
```bash
# Forward port 5000 from first machine to local 5000  
ssh -L 5000:localhost:5000 user@first-machine-ip
# Then run:
python controller.py --p2p --player J2 --my-port 5001 --opponent-port 5000 --opponent-host localhost
```

## Game Events Display

When running, you'll see event messages like:
```
[J1] UNIT_MOVE: {'unit_id': 12345, 'x': 15, 'y': 20}
[J2] BUILDING_CONSTRUCT: {'type': 'Farm', 'x': 50, 'y': 60}
```

## Troubleshooting

### Connection Issues
- Ensure both instances use different `--my-port` values
- Check `--opponent-port` matches opponent's `--my-port`
- Verify opponent is running before starting game
- Check firewall allows UDP on specified ports

### Port Already in Use
```bash
# Change port number
python controller.py --p2p --player J1 --my-port 5010 --opponent-port 5011
```

### Events Not Syncing
- Verify JSON encoding/decoding (check Print_Display output for errors)
- Ensure opponent instance is still running
- Check network connectivity between instances

## Integration Notes

The P2P system integrates with:
- **EventLogger** - Centralized event logging
- **P2PNetworkClient** - Network communication
- **game_loop_graphics()** and **game_loop_curses()** - Event sync in game loops

To add new event types, extend the `EventLogger` class with new logging methods.
