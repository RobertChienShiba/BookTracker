#!/bin/bash

dramatiq src.bg_task > worker.log 2>&1 
echo "Dramatiq worker started and logging to worker.log"