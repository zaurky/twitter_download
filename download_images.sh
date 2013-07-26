#!/bin/bash

BASEDIR=$(dirname $0)

cd $BASEDIR

source workspace/bin/activate; PYTHONPATH=$BASEDIR python bin/download_image.py && fdupes -r -1 images 2> /dev/null | awk '{print $2}' | xargs rm -f -; deactivate

