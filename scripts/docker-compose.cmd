@echo off
wsl -d Ubuntu-24.04 -e docker compose %*
