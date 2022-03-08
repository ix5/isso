#!/usr/bin/env bash

# Generate Javascript client files
docker build -f docker/Dockerfile-js -t isso-js .
# Generate production image
docker build -f docker/Dockerfile-production -t isso .
