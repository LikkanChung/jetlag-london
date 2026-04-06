import csv
import math
import util

MAP_NAME = 'tfl-zone-1-and-2'
INPUT_FILE = 'maps/tfl-zone-1-and-2.csv'
OUTPUT_FILE = 'maps/tfl-zone-1-and-2-hiding-zones.csv'
BORDER_OUTPUT_FILE = 'maps/tfl-zone-1-and-2-border.csv'

HIDING_ZONE_RADIUS_LAT = 0.00363  # 1/4 mile in degrees (vertical)
HIDING_ZONE_RADIUS_LON = 0.00583  # 1/4 mile in degrees (horizontal at latitude 51.5079)
HIDING_ZONE_POLYGON_EDGES = 72

locations = util.parse_wkt_points_csv(INPUT_FILE)

# get the latitude/longitude of each location, and create a hiding zone polygon around it
hiding_zones = []
border_points = []
for location in locations:  
    latitude = location['latitude']
    longitude = location['longitude']

    # create a circular polygon around the point
    polygon_points = []
    for i in range(HIDING_ZONE_POLYGON_EDGES):
        angle = (i / HIDING_ZONE_POLYGON_EDGES) * 360

        offset_latitude = HIDING_ZONE_RADIUS_LAT * math.sin(math.radians(angle))
        offset_longitude = HIDING_ZONE_RADIUS_LON * math.cos(math.radians(angle))
        polygon_points.append((longitude + offset_longitude, latitude + offset_latitude))
    
    border_points.extend(polygon_points)

    # close the polygon by adding the first point at the end
    polygon_points.append(polygon_points[0])
    
    hiding_zones.append({
        'name': location['name'],
        'polygon': polygon_points
    })

util.write_zones_to_csv(hiding_zones, None, OUTPUT_FILE)

border = util.generate_convex_hull(border_points)

util.write_zones_to_csv(
    [{'name': 'border', 'polygon': border}],
    None, 
    BORDER_OUTPUT_FILE
)

util.write_border_points_to_csv(border, MAP_NAME)