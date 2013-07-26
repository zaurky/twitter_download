#!/usr/bin/python

import pexif
from pexif import JpegFile
import optparse


def readExif(filename):
    try:
        img = pexif.JpegFile.fromFile(filename)
    except JpegFile.InvalidFile:
        return

    if not img.exif.primary.has_key('Artist'):
        return

    print "##########################################"
    print img.exif.primary.Artist
    print "--"
    print img.exif.primary.ImageDescription
    if img.exif.primary.has_key('DateTimeOriginal'):
        print img.exif.primary.DateTimeOriginal


if __name__ == '__main__':
    parser = optparse.OptionParser(usage = "%prog filename")

    (_, args) = parser.parse_args()
    for filename in args:
        readExif(filename)
