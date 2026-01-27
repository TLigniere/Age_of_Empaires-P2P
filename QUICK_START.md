# 🎮 P2P via C Process - Quick Reference

## System Now Uses C Process Relay ✅

Events flow: **J1 → C Process → J2**

## Start C Process First

```bash
./GameP2P.exe 5000 5001 6000
```

## Terminal 1 - Player 1 (J1)

```bash
python controller.py --p2p --player J1 --my-port 5000 graphics
```

## Terminal 2 - Player 2 (J2)

```bash
python controller.py --p2p --player J2 --my-port 5001 graphics
```

## What to Expect

Both terminals should show:
```
[P2P] Client J1 configured to route through C process
[P2P] Connection established with C
[J2] UNIT_MOVE: {'unit_id': 12345, 'x': 15, 'y': 20}
[J1] BUILDING_CONSTRUCT: {'type': 'Farm', 'x': 50, 'y': 60}
```

## Event Types

- `UNIT_MOVE` - Unit movement
- `BUILDING_CONSTRUCT` - Building construction
- `UNIT_CREATE` - Unit creation
- `RESOURCE_GATHER` - Resource gathering
- `ATTACK` - Combat actions

## Architecture

```
Player 1 ──→ C Process ──→ Player 2
Player 2 ──→ C Process ──→ Player 1
```

## Key Code Changes

**P2PNetworkClient** - Now takes NetworkClient parameter:
```python
p2p = P2PNetworkClient(network_client=network, player_side='J1')
```

**Sending events** - Via C process:
```python
self.network_client.send(event_type, json_msg)
```

**Receiving events** - From C process:
```python
messages = self.network_client.consume_messages()
```

## Configuration

```python
ENABLE_NETWORK = True   # Connect to C
ENABLE_P2P = True       # Enable relay mode
P2P_PLAYER_SIDE = 'J1'  # Set via --player flag
```

## Ports

| Port | Purpose |
|------|---------|
| 5000 | J1 listens |
| 5001 | J2 listens |
| 6000 | C process |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "C not connected" | Start C process first |
| Port in use | `--my-port 5010 --opponent-port 5011` |
| No events | Verify C is running & receiving |
| Connection timeout | Check firewall, restart C |

## Files Created/Updated

- ✅ `controller.py` - Modified P2P system
- 📄 `IMPLEMENTATION_COMPLETE.md` - Full overview
- 📄 `C_PROCESS_CHANGES.md` - Detailed changes
- 📄 `P2P_C_PROCESS_RELAY.md` - Architecture docs
- 📄 `P2P_README.md` - Updated user guide

## Next: Process Events

Once running, you can enhance by:
1. Listening for opponent events
2. Updating their units/buildings
3. Validating event legality
4. Syncing resources

Example:
```python
for event in received_events:
    if event['type'] == 'UNIT_MOVE':
        update_enemy_unit(event['data'])
```

## Status

✅ **Complete** - P2P relay through C process fully implemented
