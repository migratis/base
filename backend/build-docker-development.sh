#!/bin/bash
cp docker_development/* ./
docker compose up --build
rm docker-compose.yml
rm Dockerfile
rm docker-entrypoint.sh
rm requirements.txt
