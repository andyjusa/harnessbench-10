#!/bin/sh
set -u
python /tests/verify.py
status=$?
mkdir -p /logs/verifier
[ "$status" -eq 0 ] && echo 1 > /logs/verifier/reward.txt || echo 0 > /logs/verifier/reward.txt
exit "$status"
