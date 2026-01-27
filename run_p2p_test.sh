#!/bin/bash
# P2P Multiplayer Test Script
# This script launches two game instances for local P2P testing

echo "========================================="
echo "Age of Empires P2P Multiplayer Test"
echo "========================================="
echo ""

# Check if previous instances are still running
if lsof -Pi :5000 -sTCP:LISTEN -t > /dev/null 2>&1; then
    echo "⚠️  Port 5000 is already in use. Killing previous instance..."
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

if lsof -Pi :5001 -sTCP:LISTEN -t > /dev/null 2>&1; then
    echo "⚠️  Port 5001 is already in use. Killing previous instance..."
    lsof -ti:5001 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

echo "Starting Player 1 (J1) on port 5000..."
echo "Command: python controller.py --p2p --player J1 --my-port 5000 --opponent-port 5001 graphics"
echo ""

gnome-terminal -- python controller.py --p2p --player J1 --my-port 5000 --opponent-port 5001 graphics &

sleep 2

echo "Starting Player 2 (J2) on port 5001..."
echo "Command: python controller.py --p2p --player J2 --my-port 5001 --opponent-port 5000 graphics"
echo ""

gnome-terminal -- python controller.py --p2p --player J2 --my-port 5001 --opponent-port 5000 graphics &

echo "✅ Both instances started!"
echo "Close either window to end the session."
