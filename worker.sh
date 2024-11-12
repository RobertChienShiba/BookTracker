#!/bin/bash

# 啟動 Dramatiq 的背景任務並將輸出寫入 worker.log
dramatiq src.bg_task > worker.log 2>&1 
echo "Dramatiq worker started and logging to worker.log"