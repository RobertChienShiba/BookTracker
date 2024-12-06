#!/bin/bash

VERSION=$(grep -oP '(?<=version = ")[^"]+' src/__init__.py)

apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

if sqlite3 ./bookly.db "SELECT 1" && curl -f "http://localhost:8000/api/$VERSION/docs"; then
  echo "Healthcheck complete successfully"
else
  exit 1
fi

unset VERSION
