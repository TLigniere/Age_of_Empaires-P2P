@echo off
REM P2P Multiplayer Test Script for Windows
REM This script launches two game instances for local P2P testing

echo =========================================
echo Age of Empires P2P Multiplayer Test
echo =========================================
echo.

echo Starting Player 1 (J1) on port 5000...
echo Command: python controller.py --p2p --player J1 --my-port 5000 --opponent-port 5001 graphics
echo.

start cmd /k python controller.py --p2p --player J1 --my-port 5000 --opponent-port 5001 graphics

timeout /t 2 /nobreak

echo Starting Player 2 (J2) on port 5001...
echo Command: python controller.py --p2p --player J2 --my-port 5001 --opponent-port 5000 graphics
echo.

start cmd /k python controller.py --p2p --player J2 --my-port 5001 --opponent-port 5000 graphics

echo.
echo [OK] Both instances started!
echo Close either window to end the session.
pause
