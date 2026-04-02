# Generate the verticies of the zones which are closer to one point than any other point on the map, and within 10 miles of the centre
import math
import util
from scipy.spatial import Voronoi
from shapely.geometry import Polygon

INPUT_FILE = 'maps/rail-stations.csv'
OUTPUT_FILE = 'maps/rail-stations-zones.csv'

FILE_PATHS = {
    'rail-stations': {
        'input': 'maps/rail-stations.csv',
        'output': 'maps/rail-stations-zones.csv',
        'max_distance_miles': 10,
        'merge_locations_in_output': True
    },
    'airports': {
        'input': 'maps/airports.csv',
        'output': 'maps/airports-zones.csv',
        'max_distance_miles': 30,
        'merge_locations_in_output': True
    }
}


# get the lat/lon of each location, and create a voronoi zone polygon around it

def generate_boundary_circle(center_lon, center_lat, radius_miles, num_points=72):
    """Generate a circle of lat/lon points at a given radius using the haversine inverse formula"""
    circle_points = []
    d = radius_miles / 3959.0  # angular distance in radians
    lat1 = math.radians(center_lat)
    lon1 = math.radians(center_lon)
    for i in range(num_points):
        bearing = math.radians(i * 360 / num_points)
        lat2 = math.asin(math.sin(lat1) * math.cos(d) + math.cos(lat1) * math.sin(d) * math.cos(bearing))
        lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(d) * math.cos(lat1),
                                  math.cos(d) - math.sin(lat1) * math.sin(lat2))
        circle_points.append((math.degrees(lon2), math.degrees(lat2)))
    return circle_points


def generate_voronoi_zones(locations, max_distance_miles=10):
    """Generate Voronoi zones for each location, clipped to a circle around the centre"""
    points = [[loc['longitude'], loc['latitude']] for loc in locations]

    # Calculate centre of all points
    center_lon = sum(p[0] for p in points) / len(points)
    center_lat = sum(p[1] for p in points) / len(points)

    # Scale longitude by cos(lat) so Voronoi bisectors are correct at this latitude
    cos_lat = math.cos(math.radians(center_lat))

    scaled_points = [[p[0] * cos_lat, p[1]] for p in points]

    # Add far-away dummy points so all real regions become finite
    far = 1.0  # ~69 miles in degrees, well beyond clipping boundary
    dummy_points = [
        [center_lon * cos_lat - far, center_lat - far],
        [center_lon * cos_lat + far, center_lat - far],
        [center_lon * cos_lat - far, center_lat + far],
        [center_lon * cos_lat + far, center_lat + far],
    ]
    all_points = scaled_points + dummy_points

    # Create boundary circle
    boundary = Polygon(generate_boundary_circle(center_lon, center_lat, max_distance_miles))

    # Create Voronoi diagram in scaled space
    vor = Voronoi(all_points)

    zones = []
    for i, loc in enumerate(locations):  # only iterate real locations, skip dummies
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]

        if not region or -1 in region:
            continue

        # Unscale longitude back to real lon/lat
        polygon_points = [(vor.vertices[v][0] / cos_lat, vor.vertices[v][1]) for v in region]

        poly = Polygon(polygon_points)
        if not poly.is_valid:
            poly = poly.buffer(0)
        clipped = poly.intersection(boundary)
        if not clipped.is_empty and clipped.geom_type == 'Polygon':
            coords = list(clipped.exterior.coords)[:-1]  # shapely closes rings; drop duplicate
            if len(coords) >= 3:
                zones.append({
                    'name': loc['name'],
                    'polygon': coords
                })

    return zones

    
for layer in FILE_PATHS:
    input_file = FILE_PATHS[layer]['input']
    output_file = FILE_PATHS[layer]['output']
    max_distance_miles = FILE_PATHS[layer]['max_distance_miles']
    merge_locations_in_output = FILE_PATHS[layer]['merge_locations_in_output']
    locations = util.parse_wkt_points_csv(input_file)
    zones = generate_voronoi_zones(locations, max_distance_miles=max_distance_miles)
    util.write_zones_to_csv(
        zones, 
        locations if merge_locations_in_output else None,  # pass locations for merging pins if enabled
        output_file)