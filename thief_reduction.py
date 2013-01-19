#!/usr/bin/env python

import json, time, random, datetime, csv, urllib, cv
import numpy as np
from pprint import pprint
from housepy import net, science, drawing, util, log
from openpaths_video import *

LON = 0
LAT = 1
T = 2
X = 3
Y = 4

ZOOM = 0.03
ZOOM = 10000

image_id = 0

if not os.path.isdir("sv_images"):
    os.mkdir("sv_images")    

points = []
for i, line in enumerate(open("pulled_points.txt").readlines()):
    if i % 2 == 0:      # things are double in the list for some reason
        points.append([(float(p) if p != "None" else None) for p in line.strip().split(' ')])

points = np.array(points)
median_lon = np.median(points[:,0])
median_lat = np.median(points[:,1])
points = np.array([point for point in points if abs(point[0] - median_lon) < ZOOM and abs(point[1] - median_lat) < ZOOM])    
max_lon = np.max(points[:,0])
min_lon = np.min(points[:,0])
max_lat = np.max(points[:,1])
min_lat = np.min(points[:,1])

points = list(points)
for point in points:
    point[X] = util.scale(point[LON], min_lon, max_lon)
    point[Y] = util.scale(point[LAT], min_lat, max_lat)



def get_streetview(heading, point=None, panoid=None):
    """For a lat/lon pair, pull Google Streetview panorama data and stitch together the choice tiles"""
    if point is not None:
        panoid_url = "http://cbk0.google.com/cbk?output=json&ll=%s,%s" % (point[LAT], point[LON])
    elif panoid is not None:
        panoid_url = "http://cbk0.google.com/cbk?output=json&panoid=%s" % panoid
    # print(panoid_url)
    try:
        connection = urllib2.urlopen(panoid_url)
        json_data = json.loads(''.join(connection.readlines()))
        panoid = json_data['Location']['panoId']
        lon, lat = float(json_data['Location']['lng']), float(json_data['Location']['lat'])
        yaw = float(json_data['Projection']['pano_yaw_deg'])
        alt_yaw = (yaw + 180) % 360
        links = json_data['Links']
    except Exception as e:
        print("JSON download failed: %s" % panoid_url)
        print(log.exc(e))
        return None
        
    get_image(panoid, heading, yaw, alt_yaw)    

    return (lon, lat), get_closest_link(links, heading)


def get_closest_link(links, heading):
    min_difference = 1000
    next_panoid = None
    next_heading = None
    for l, link in enumerate(links):
        link_heading = float(link['yawDeg'])
        difference = science.angular_difference(link_heading, heading)        
        # print("--> %f (%f)" % (link_heading, difference))        
        if difference < min_difference:
            min_difference = difference
            next_heading = link_heading
            next_panoid = link['panoId']
    print("LINK HEADING: %s" % next_heading)     
    if min_difference > 90:
        return None
    else:           
        return next_panoid        
    
    
def get_image(panoid, heading, yaw, alt_yaw):
    yaw_dist = science.angular_difference(yaw, heading)
    alt_dist = science.angular_difference(alt_yaw, heading)        

    if yaw_dist <= alt_dist:
        url_left = "http://cbk0.google.com/cbk?output=tile&panoid=%s&zoom=3&x=2&y=1" % panoid
        url_right = "http://cbk0.google.com/cbk?output=tile&panoid=%s&zoom=3&x=3&y=1" % panoid
    else:
        url_left = "http://cbk0.google.com/cbk?output=tile&panoid=%s&zoom=4&x=12&y=3" % panoid
        url_right = "http://cbk0.google.com/cbk?output=tile&panoid=%s&zoom=4&x=0&y=3" % panoid
        
    filepath_left = "sv_images/%s_left.jpg" % i
    filepath_right = "sv_images/%s_right.jpg" % i
    try:
        urllib.urlretrieve(url_left, filepath_left)
        urllib.urlretrieve(url_right, filepath_right)        
    except Exception as e:
        print("Image download failed")
        return None, None    
    image_left = Image.open(filepath_left)        
    image_right = Image.open(filepath_right)    
    image = Image.new('RGB', (1024, 512))
    image.paste(image_left, (0, 0))
    image.paste(image_right, (512, 0))        
    os.remove(filepath_left)
    os.remove(filepath_right)
    
    global image_id
    filepath = "sv_images/%s.png" % image_id
    image.save(filepath, 'PNG')
    image_id += 1
    
    cv.ShowImage("streetview", drawing.pil_to_ipl(image))                
    cv.WaitKey(5)    
    print(url_left)
    print(url_right)                                    
        

    
ctx = drawing.Context(1000, 1000, relative=True, flip=True, hsv=True)

while True:

    ctx.clear()

    for p, point in enumerate(points):
        ctx.arc(point[X], point[Y], 3 / ctx.width, thickness=1.0, stroke=(0.0, 0.0, 0.0))          
        pass
        
    path_index = 0

    while True:

        print("----------")        

        origin = points[path_index]
        destination = points[path_index + 1]
        ctx.arc(origin[X], origin[Y], 3 / ctx.width, thickness=1.0, fill=(0.0, 0.0, 0.0))
        ctx.arc(destination[X], destination[Y], 3 / ctx.width, thickness=1.0, fill=(0.33, 1.0, 1.0))
        ctx.line(origin[X], origin[Y], destination[X], destination[Y], stroke=(0.0, 0.0, 0.5))        
        ctx.frame()
        time.sleep(1)        

        heading = science.heading((origin[X], origin[Y]), (destination[X], destination[Y]))
        real_heading = heading
        print("REAL HEADING: %s" % heading)            
                    
        fake_points = []                 
        result = get_streetview(heading, point=origin)           
        if result is not None:            
            fake_point, next_panoid = result 
            fake_points.append(str(fake_point))
            while next_panoid is not None:
                print("--")
                x = util.scale(fake_point[LON], min_lon, max_lon)
                y = util.scale(fake_point[LAT], min_lat, max_lat)
                ctx.arc(x, y, 3 / ctx.width, thickness=0.0, fill=(0.55, 1.0, 1.0))    
                ctx.frame()
                # time.sleep(1)
                                
                fake_heading = science.heading((x, y), (destination[X], destination[Y]))
             
                print((x, y))
                print((destination[X], destination[Y]))
                print("FAKE HEADING: %s" % fake_heading)            
                
                
                fake_point, next_panoid = get_streetview(fake_heading, panoid=next_panoid)
                if str(fake_point) in fake_points and fake_points.index(str(fake_point)) != len(fake_points) - 1:
                    break
                fake_points.append(str(fake_point))                    


        path_index += 1
        if path_index == len(points) - 1:
            break

        ctx.frame()    
        
    break    
        

