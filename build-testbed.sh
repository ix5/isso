#!/usr/bin/env bash

# Generate Javascript client files
docker build -f docker/Dockerfile-js -t isso-js .
# Download Jest and puppeteer files
docker build -f docker/Dockerfile-js-puppeteer -t isso-js-puppeteer .

# Prepare testbed image
docker build -f docker/Dockerfile-js-testbed -t isso-js-testbed .
