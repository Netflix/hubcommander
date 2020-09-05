#!/bin/bash
echo "$DHUB_PASS" | docker login -u "$DHUB_USERNAME" --password-stdin
docker push seanngan7/hubcommander
