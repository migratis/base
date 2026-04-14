#!/bin/bash
cp docker_local/* ./
docker compose up --build
rm docker-compose.yml
rm Dockerfile
rm docker-entrypoint.sh
rm requirements.txt
