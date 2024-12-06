#!/bin/bash

if sqlite3 ./bookly.db "SELECT 1" && curl -f "http://localhost:8080/api/$VERSION/docs"; then
  echo "Healthcheck complete successfully"
else
  exit 1
fi
