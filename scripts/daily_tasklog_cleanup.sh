#!/bin/bash
# 每日 0 点维护：tasklog 昨日段 → F0 (≤7KB) + workspace 清理昨日/初始化今日
# no_agent cron 调用，stdout 原样记录到 cron output
cd "$HOME/AppData/Local/hermes/scripts" || exit 1
python mem_tasklog.py compress
python mem_tasklog.py init
