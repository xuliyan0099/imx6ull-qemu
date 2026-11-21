#!/bin/bash
BASE=http://127.0.0.1:8767
T=$(curl -s "$BASE/token" | sed -n 's/.*"token": *"\([^"]*\)".*/\1/p')
curl -s -H "X-Token: $T" "$BASE/api/serial" > /tmp/im6-live-serial.json
python3 - <<'PY'
import json,re
text=json.load(open('/tmp/im6-live-serial.json'))['text']
for line in text.splitlines():
    if re.search(r'ci_hdrc|usb|audio|sound|ALSA|No soundcards', line, re.I):
        print(line)
PY
echo "---qemu log---"
LOG=$(find /tmp -maxdepth 2 -path '*im6-board*' -name qemu.log -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
echo "$LOG"
tail -20 "$LOG"
