#!/bin/bash
# Quick run script for daily-push
# Usage:
#   ./run.sh                # print only (no webhook)
#   ./run.sh <webhook_url>  # send to Feishu/Lark

WEBHOOK="${1:-}"

if [ -n "$WEBHOOK" ]; then
    docker run --rm -e FEISHU_WEBHOOK="$WEBHOOK" daily-push:latest
else
    docker run --rm daily-push:latest
fi
