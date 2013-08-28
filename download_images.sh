#!/bin/bash

BASEDIR=$(dirname $0)

cd $BASEDIR

source workspace/bin/activate; PYTHONPATH=$BASEDIR python bin/download_image.py; deactivate

# should add a non duplicate script, but jpg files contain tweet as exif, and that change from one to the other

