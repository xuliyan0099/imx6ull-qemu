#!/bin/bash
BASE=http://127.0.0.1:8767
T=$(curl -s "$BASE/token" | sed -n 's/.*"token": *"\([^"]*\)".*/\1/p')
curl -s -H "X-Token: $T" "$BASE/api/status"; echo
