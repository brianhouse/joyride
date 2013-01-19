#!/usr/bin/env python

import json, time, random, datetime, csv, urllib
import numpy as np
from pprint import pprint
from housepy import net, science, drawing, util
from openpaths_video import *

LON = 0
LAT = 1
T = 2
X = 3
Y = 4

ZOOM = 1000
DURATION = 60*30    # if points are within 10 minutes, group them
THRESHOLD = 3       # less than threshold points isnt much of a path


points = json.loads(open("thief_points.json").read())
points = np.array([(float(point['lon']), float(point['lat']), time.mktime(util.parse_date(point['time']).timetuple()), None, None) for point in points])

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

all_points = []

# should also print out the directions
instructions = []

def get_fake_points(origin, destination):
    all_points.append(origin)
    params = {  'origin': "%s,%s" % (origin[LAT], origin[LON]),
                'destination': "%s,%s" % (destination[LAT], destination[LON]),
                'mode': "driving",
                # 'avoid': "highways",
                'sensor': "false"
                }
    params = net.urlencode(params)
    url = "http://maps.googleapis.com/maps/api/directions/json?" + params
    response = net.read(url)
    directions = json.loads(response)
    try:
        steps = directions['routes'][0]['legs'][0]['steps']  
    except Exception as e:
        print(response)
        exit()    
    points = []
    for i, step in enumerate(steps):
        instruction = step['html_instructions']
        instructions.append(instruction)
        if i != 0:
            point = [step['start_location']['lng'], step['start_location']['lat'], None, None, None]
            points.append(point)
        if i != len(steps) - 1:    
            point = [step['end_location']['lng'], step['end_location']['lat'], None, None, None]
            points.append(point)
    for point in points:
        point[X] = util.scale(point[LON], min_lon, max_lon)
        point[Y] = util.scale(point[LAT], min_lat, max_lat) 
        all_points.append(point)
    all_points.append(destination)               
    return points
        
fake_points = []        
for i, destination in enumerate(points):
    if i == 0:
        continue
    origin = points[i-1]
    fake_points.extend(get_fake_points(origin, destination))
    print('.')
    time.sleep(1.0)

print("instruction length: %s" % len(instructions))    
print('\n'.join(instructions))

print("ALL POINTS")
for point in all_points:
    print point
    
print
print    


ctx = drawing.Context(1000, 1000, relative=True, flip=True, hsv=True)

while True:
    
    ctx.clear()
        
    # draw real points
    print("REAL POINTS")
    for point in points:
        print point
        ctx.arc(point[X], point[Y], 3 / ctx.width, thickness=1.0, fill=(0.0, 0.0, 0.0))          

    print

    # draw fake points
    print("FAKE POINTS")
    for point in fake_points:
        print point
        ctx.arc(point[X], point[Y], 3 / ctx.width, thickness=1.0, stroke=(0.0, 0.0, 0.5))          

    path_index = 0

    while True:

        # draw path
        origin = all_points[path_index]
        destination = all_points[path_index + 1]
        ctx.line(origin[X], origin[Y], destination[X], destination[Y], stroke=(0.0, 0.0, 0.5))
    
        path_index += 1
        if path_index == len(all_points) - 1:
            break

        ctx.frame()



def get_streetviews(points):
    """For each lat/lon pair, pull Google Streetview panorama data and stitch together the choice tiles"""

    if not os.path.isdir("sv_images"):
        os.mkdir("sv_images")    
    for i, point in enumerate(points):    
        print("----------")        
        panoid_url = "http://cbk0.google.com/cbk?output=json&ll=%s,%s" % (point[LAT], point[LON])
        try:
            connection = urllib2.urlopen(panoid_url)
            json_data = json.loads(''.join(connection.readlines()))
            panoid = json_data['Location']['panoId']
        except Exception as e:
            print("JSON download failed: %s" % panoid_url)
            continue            
        url_left = "http://cbk0.google.com/cbk?output=tile&panoid=%s&zoom=3&x=2&y=1" % panoid
        url_right = "http://cbk0.google.com/cbk?output=tile&panoid=%s&zoom=3&x=3&y=1" % panoid
        filepath_left = "sv_images/%s_left.jpg" % i
        filepath_right = "sv_images/%s_right.jpg" % i
        try:
            urllib.urlretrieve(url_left, filepath_left)
            urllib.urlretrieve(url_right, filepath_right)        
        except Exception as e:
            print("Image download failed")
            continue    
        image_left = Image.open(filepath_left)        
        image_right = Image.open(filepath_right)    
        image = Image.new('RGB', (1024, 512))
        image.paste(image_left, (0, 0))
        image.paste(image_right, (512, 0))        
        os.remove(filepath_left)
        os.remove(filepath_right)
        filepath = "sv_images/%s.png" % i
        image.save(filepath, 'PNG')
        print(panoid_url)
        print(url_left)
        print(url_right)                                    
    if not len(points):
        print("No points!")
        exit()
        
# get_streetviews(points)
# generate_video()
