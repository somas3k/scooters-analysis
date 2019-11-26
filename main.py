import math
import datetime
from time import mktime, sleep
import operator
from functools import reduce
import requests
from node_fetcher import NodesFetcher


def distance(coord1, coord2):
    R = 6372800  # Earth radius in meters
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def calculate_min_max_average_difference_between_scooters_and_pois(data):
    min_distance = 999999
    max_distance = 0
    distance_sum = 0
    for value in data:
        [scooter_lat, scooter_lon, poi_lat, poi_lon] = value
        dis = distance((scooter_lat, scooter_lon), (poi_lat, poi_lon))
        if dis < min_distance:
            min_distance = dis
        if dis > max_distance:
            max_distance = dis
        distance_sum += dis

    avg = distance_sum / len(data)
    return min_distance, max_distance, avg


TRACK_DURATION_LIMIT = 24 * 60  # minutes
DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def calculate_duration(track: dict):
    start_time = datetime.datetime.strptime(track['from']['stays_at']['to'], DATE_TIME_FORMAT)
    end_time = datetime.datetime.strptime(track['to']['stays_at']['from'], DATE_TIME_FORMAT)

    return (mktime(end_time.timetuple()) - mktime(start_time.timetuple())) / 60


def filter_too_long_tracks(tracks: list):
    filtered_tracks = []
    filtered_out_tracks = []
    for track in tracks:
        if calculate_duration(track) <= TRACK_DURATION_LIMIT:
            filtered_tracks.append(track)
        else:
            filtered_out_tracks.append(track)
    return filtered_tracks, filtered_out_tracks


def filter_too_long_tracks_for_scooters(scooter_to_tracks: dict):
    filtered_scooter_to_tracks = {}
    filtered_out_scooter_to_tracks = {}
    for scooter, tracks in scooter_to_tracks.items():
        filtered_scooter_to_tracks[scooter], filtered_out_scooter_to_tracks[scooter] = filter_too_long_tracks(tracks)
    return filtered_scooter_to_tracks, filtered_out_scooter_to_tracks


def fuelLevel_diff(track):
    fuelLevel_before = int(track['from']['stays_at']['fuelLevel'])
    fuelLevel_after = int(track['to']['stays_at']['fuelLevel'])

    return fuelLevel_before - fuelLevel_after


def divide_by_used_and_charging(tracks):
    were_used = []
    were_charging = []
    for track in tracks:
        if fuelLevel_diff(track) < 0:
            were_charging.append(track)
        else:
            were_used.append(track)
    return were_used, were_charging


def divide_tracks_for_scooters_by_used_and_charging(scooter_to_tracks: dict):
    were_used = {}
    were_charging = {}
    for scooter, tracks in scooter_to_tracks.items():
        were_used[scooter], were_charging[scooter] = divide_by_used_and_charging(tracks)

    return were_used, were_charging


def get_coord_as_string(point: dict):
    return '{lat},{lon}'.format(lat=point['stays_at']['exactLat'], lon=point['stays_at']['exactLon'])


REQUEST_URL = 'http://dev.virtualearth.net/REST/v1/Routes/Walking'
PARAMS = {
    'optimize': 'distance',
    'maxSolutions': '1',
    'key': 'Arq_YCOmhrZbndvDY0hrjqK_e6dvTuluWhNY8Jdd1AiV1WTCJm2rDPNI9Ckgv5EX',
    'routeAttributes': 'routeSummariesOnly'
}


def get_walking_distance(from_dict, to_dict):
    PARAMS['wayPoint.1'] = get_coord_as_string(from_dict)
    PARAMS['wayPoint.2'] = get_coord_as_string(to_dict)

    i = int(
        requests.get(url=REQUEST_URL, params=PARAMS).json()["resourceSets"][0]["resources"][0]["travelDistance"] * 1000)

    return i


def calculate_min_max_avg_track_distance(tracks: list):
    min_distance = 99999999
    max_distance = 0
    distance_sum = 0

    for i, track in enumerate(tracks):
        dist = get_walking_distance(track['from'], track['to'])
        if dist < min_distance:
            min_distance = dist
        if dist > max_distance:
            max_distance = dist
        distance_sum += dist
        sleep(0.5)
        print('Completion: {:0.2f}'.format((i/len(tracks))*100))
    return min_distance, max_distance, distance_sum / len(tracks)


a = NodesFetcher("bolt://192.168.56.102", "neo4j", "hive")

# print(calculate_min_max_average_difference_between_scooters_and_pois(
#     a.get_data_to_check_distance_between_scooters_and_pois()))
# print(a.get_tracks()[12514])
filtered, filtered_out = filter_too_long_tracks_for_scooters(a.get_tracks())
a.close()
used, charging = divide_tracks_for_scooters_by_used_and_charging(filtered)
min_dist, max_dist, avg = calculate_min_max_avg_track_distance(list(reduce(operator.concat, list(used.values()))))
print(min_dist, max_dist, avg)

