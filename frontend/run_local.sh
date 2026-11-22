#!/usr/bin/env bash
cd "$(dirname "$0")"
python3 -m http.server 5500 --bind 127.0.0.1
