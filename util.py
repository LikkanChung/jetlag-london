import re
import csv


# regex for WKT point which the cooridinates are in the format "POINT (lon lat)" and could also be in exponent format like "POINT (1.234567e-5 1.234567e-5)"
WKT_POINT_REGEX = r'POINT\s?\((-?\d+\.?\d*(?:[eE][+-]?\d+)?) (-?\d+\.?\d*(?:[eE][+-]?\d+)?)\)'


def wkt_point_to_latitude_longitude(wkt_point):
    match = re.match(WKT_POINT_REGEX, wkt_point)
    if match:
        latitude = float(match.group(2))
        longitude = float(match.group(1))
        return longitude, latitude
    else:
        raise ValueError(f"Invalid WKT point format: {wkt_point}")


def format_as_wkt_polygon(polygon_points):
    if not polygon_points:
        raise ValueError("Polygon must contain at least one point")

    # WKT polygon rings must be closed (first point equals last point).
    ring = list(polygon_points)
    if ring[0] != ring[-1]:
        ring.append(ring[0])

    wkt_polygon = "POLYGON(("
    wkt_polygon += ", ".join([f"{lon} {lat}" for lon, lat in ring])
    wkt_polygon += "))"
    return wkt_polygon


def parse_wkt_points_csv(csv_file):
    locations = []
    with open(csv_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            lon, lat = wkt_point_to_latitude_longitude(row['WKT'])
            locations.append({
                'name': row['name'],
                'wkt_point': row['WKT'],
                'latitude': lat,
                'longitude': lon,
                'group': row.get('group')  # optional group field for merging pins in output
            })
    return locations


def parse_wkt_points_groups_csv(csv_file):
    groups = {}
    with open(csv_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            lon, lat = wkt_point_to_latitude_longitude(row['WKT'])
            group_name = row['group']
            if group_name not in groups:
                groups[group_name] = []
            groups[group_name].append({
                'name': row['name'],
                'wkt_point': row['WKT'],
                'latitude': lat,
                'longitude': lon
            })
    return groups


def write_zones_to_csv(
        zones, 
        locations,  # if locations is provided, add the location points to the CSV too
        output_file):
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['name', 'WKT', 'group'] 
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for zone in zones:
            writer.writerow({
                'name': zone['name'],
                'WKT': format_as_wkt_polygon(zone['polygon']),
                'group': zone.get('group')  # include group in output if it exists for merging pins in output
            })
        if locations:
            for loc in locations:
                writer.writerow({
                    'name': loc['name'],
                    'WKT': loc['wkt_point'],
                    'group': loc.get('group')  # include group in output if it exists for merging pins in output
                })