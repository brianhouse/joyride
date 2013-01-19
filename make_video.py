#!/usr/bin/env python

import os, oauth2, time, urllib, urllib2, json, cv
from PIL import Image, ImageStat
from cv import CV_FOURCC    

FPS = 30
IMAGE_FPS = 10
SIZE = 1024, 512
FILENAME = "streetview.mov"
CODEC = CV_FOURCC('M', 'P', '4', '2')
COLOR = True


def generate_video():
    """Generate a video from the image sequence, using OpenCV"""
    writer = cv.CreateVideoWriter(FILENAME, CODEC, FPS, SIZE, COLOR)
    files = []
    for filename in os.listdir("sv_images"):
        if filename[-4:] != ".png":
            continue
        files.append(filename)
    files.sort(key=alphanum_key)    
    for filename in files:        
        path = "sv_images/%s" % filename
        image = Image.open(path)
        stats = ImageStat.Stat(image)
        print path,
        print sum(stats.sum), 
        if sum(stats.sum) == 0:      # image is all black, skip it
            print "--> skipped"
            continue
        print "--> ok"    
        image = pil_to_ipl(image)
        for i in xrange(FPS / IMAGE_FPS):
            cv.WriteFrame(writer, image)
        
def pil_to_ipl(pil_image):
    """Convert a PIL image to ipl (OpenCV)"""    
    import cv
    cv_image = cv.CreateImageHeader(pil_image.size, cv.IPL_DEPTH_8U, 3)
    cv.SetData(cv_image, pil_image.rotate(180).tostring()[::-1])
    return cv_image

def alphanum_key(s):
    """Turn a string into a list of string and number chunks."""
    import re
    return [tryint(c) for c in re.split('([0-9]+)', s)]

def tryint(s):
    try:
        return int(s)
    except:
        return s



generate_video()