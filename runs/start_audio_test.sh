#!/bin/bash
BASE=http://127.0.0.1:8767
T=$(curl -s "$BASE/token" | sed -n 's/.*"token": *"\([^"]*\)".*/\1/p')
echo "token=$T"
curl -s -X POST -H "X-Token: $T" -H 'Content-Type: application/json' \
  -d '{"profile":"linux-official"}' "$BASE/api/start"
echo
