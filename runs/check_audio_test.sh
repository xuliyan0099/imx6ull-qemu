#!/bin/bash
BASE=http://127.0.0.1:8767
T=$(curl -s "$BASE/token" | sed -n 's/.*"token": *"\([^"]*\)".*/\1/p')
sleep 35
echo "---status---"
curl -s -H "X-Token: $T" "$BASE/api/status"; echo
echo "---serial tail---"
curl -s -H "X-Token: $T" "$BASE/api/serial" | sed 's/\\r//g' | tail -c 6000
echo
echo "---audio file---"
ls -l /tmp/im6-audio.wav 2>/dev/null || true
