# Running tests with docker

First, ensure all images are built:
```bash
./build-testbed.sh
```
This will take some time as headless chromium needs to be downloaded, once
(~400Mb), as well as necessary libraries installed. Will be cached on subsequent
runs.

Start up server part via `docker-compose`:
```bash
docker-compose up -d
```

Then, run unit and integration tests:
```bash
docker run isso-js-testbed npm run test-unit
docker run --network container:isso-server isso-js-testbed npm run test-integration
```

Finally, bring down the server again
```bash
docker-compose down
```

# Generate production image
The production image is based on Alpine Linux and should weigh in at about 75Mb.

Run `./build-prod.sh`.

Use via `docker run --rm -d isso:latest`.
