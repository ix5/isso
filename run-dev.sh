#!/usr/bin/env bash

# Generate Javascript client files
docker build -f docker/Dockerfile-js -t isso-js .
# Generate dev image
docker build -f docker/Dockerfile-dev -t isso-dev .

# Run dev image
docker run -it \
    -p 8080:8080 \
    -v $PWD/isso:/src/isso/ \
    -v $PWD/share:/src/share/ \
    -v $PWD/config:/config:ro \
    -v $PWD/db:/db isso-dev \
    /isso/bin/isso -c /config/isso.cfg run
