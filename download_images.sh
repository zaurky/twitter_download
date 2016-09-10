#!/bin/bash

BASEDIR=$(dirname $0)
LOCK="/tmp/download_image.lock"

cd $BASEDIR

if [ ! -f $LOCK ]; then
    touch $LOCK
    source workspace/bin/activate;
    PYTHONPATH=$BASEDIR python bin/download_image.py > /tmp/download_image.log 2> /tmp/download_image.err;
    deactivate;
    rm -f $LOCK
fi

# should add a non duplicate script, but jpg files contain tweet as exif, and that change from one to the other

