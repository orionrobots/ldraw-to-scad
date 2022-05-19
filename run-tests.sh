#!/bin/bash
docker run --rm -v ${PWD}:/mnt/src python:3.9 bash -ceu "
  cd /mnt/src &&
  pip install -r test-requirements.txt &&
  pip install -e .
  python -m pytest
  python -m pylint src tests ldraw2scad
  python -m pycodestyle src tests ldraw2scad
  python -m build
"
