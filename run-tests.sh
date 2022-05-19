#!/bin/bash
docker run --rm -v ${PWD}:/mnt/src python:3.9 bash -ceu "
  cd /mnt/src &&
  pip install -r test-requirements.txt &&
  pytest .
"
