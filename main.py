import json
import math
import datetime
from time import mktime, sleep
import random
import operator
from functools import reduce
import itertools
import scipy
from scipy import stats
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

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


TRACK_DURATION_LIMIT = 3 * 60  # minutes
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


def get_from_coords(track):
    return track['from']['stays_at']['exactLat'], track['from']['stays_at']['exactLon']


def get_to_coords(track):
    return track['to']['stays_at']['exactLat'], track['to']['stays_at']['exactLon']


def distance_of_track(track):
    coord1 = get_from_coords(track)
    coord2 = get_to_coords(track)
    return distance(coord1, coord2)


def is_diff_at_location(track):
    dist = distance_of_track(track)
    return dist > 20


def divide_by_used_charging_and_in_transport(tracks):
    were_used = []
    were_charging = []
    were_in_transport = []
    were_discharging_and_not_used = []
    were_teleported = []

    for track in tracks:
        diff = fuelLevel_diff(track)
        dist = distance_of_track(track)
        duration = calculate_duration(track)
        if diff < 0:
            were_charging.append(track)
        else:
            if diff == 0 or (diff == 1 and dist > 20):
                were_in_transport.append(track)
            else:
                if diff >= 1 and not is_diff_at_location(track):
                    were_discharging_and_not_used.append(track)
                else:
                    if float(dist) / duration > 500:
                        were_teleported.append(track)
                    else:
                        t = float(diff) / duration
                        if 20 > t > 0.03333333:
                            were_used.append(track)

    return were_used, were_charging, were_in_transport, were_discharging_and_not_used, were_teleported


def divide_tracks_for_scooters_by_used_and_charging(scooter_to_tracks: dict):
    were_used = {}
    were_charging = {}
    were_in_transport = {}
    were_discharging_and_not_used = {}
    were_teleported = {}
    for scooter, tracks in scooter_to_tracks.items():
        were_used[scooter], were_charging[scooter], were_in_transport[
            scooter], were_discharging_and_not_used[scooter], were_teleported[scooter] = divide_by_used_charging_and_in_transport(tracks)

    return were_used, were_charging, were_in_transport, were_discharging_and_not_used, were_teleported


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

    # print('Calculating for {c1}, {c2}'.format(c1=get_coord_as_string(from_dict), c2=get_coord_as_string(to_dict)))
    response = None
    try:
        response = requests.get(url=REQUEST_URL, params=PARAMS).json()
        i = int(
            response["resourceSets"][0]["resources"][0]["travelDistance"] * 1000)
        return i
    except Exception:
        if response:
            print(PARAMS)
            print(response)
            return None
        sleep(0.5)
        return None


def calculate_min_max_avg_track_distance(tracks: list):
    min_distance = 99999999
    max_distance = 0
    distance_sum = 0

    for i, track in enumerate(tracks):
        dist = track['distance']
        # dist = get_walking_distance(track['from'], track['to'])
        if dist < min_distance:
            min_distance = dist
            print('==========================' + str(min_distance) + '=======================')
        if dist > max_distance:
            max_distance = dist
        distance_sum += dist
        # sleep(0.5)
        print('Completion: {:0.2f}'.format((i / len(tracks)) * 100))
    return min_distance, max_distance, distance_sum / len(tracks)


def calculate_scooter_usages_all_time(tracks: dict):
    scooter_usages = []
    for scooter, tracks in tracks.items():
        scooter_usages.append((scooter, len(tracks)))
    return scooter_usages


def get_the_most_commonly_used_scooters(scooter_usages: list, n=10):
    scooter_usages.sort(key=lambda v: v[1], reverse=True)
    return scooter_usages[:n]


def create_bar_chart_with_usage_of_scooters(used: dict):
    scooter_usages = calculate_scooter_usages_all_time(used)
    most_used = get_the_most_commonly_used_scooters(scooter_usages, 20)
    objects = [scooter_id for (scooter_id, usages) in most_used]
    y_pos = np.arange(len(objects))
    usage = [usages for (scooter_id, usages) in most_used]
    plt.barh(y_pos, usage, align='center', alpha=0.5)
    plt.yticks(y_pos, objects)
    plt.xlabel('Usage')
    plt.show()


def get_day_of_week_from_track(track: dict):
    date = datetime.datetime.strptime(track['from']['stays_at']['to'], DATE_TIME_FORMAT)
    return date.weekday()


def get_hour_from_track(track: dict):
    date = datetime.datetime.strptime(track['from']['stays_at']['to'], DATE_TIME_FORMAT)
    return date.hour

DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def calculate_usages_grouped_by_hours(used_all: list):
    used_all.sort(key=get_hour_from_track)
    hours_with_usages = []

    for k, group in itertools.groupby(used_all, key=get_hour_from_track):
        hours_with_usages.append((k, len(list(group))))

    objects = [hour for (hour, usages) in hours_with_usages]
    y_pos = np.arange(len(objects))
    usage = [usages for (weekday, usages) in hours_with_usages]
    plt.barh(y_pos, usage, align='center', alpha=0.5)
    plt.yticks(y_pos, objects)
    plt.xlabel('Usage')
    plt.show()


def calculate_usages_grouped_by_weekday(used_all: list):
    used_all.sort(key=get_day_of_week_from_track)
    weekdays_with_usages = []

    for k, group in itertools.groupby(used_all, key=get_day_of_week_from_track):
        weekdays_with_usages.append((k, len(list(group))))

    objects = [DAYS_OF_WEEK[weekday] for (weekday, usages) in weekdays_with_usages]
    y_pos = np.arange(len(objects))
    usage = [usages for (weekday, usages) in weekdays_with_usages]
    plt.barh(y_pos, usage, align='center', alpha=0.5)
    plt.yticks(y_pos, objects)
    plt.xlabel('Usage')
    plt.show()


def get_avg_dist_from_group(group):
    return np.array([track['distance'] for track in group]).mean()


def calculate_avg_distance_grouped_by_weekday(used_all: list):
    used_all.sort(key=get_day_of_week_from_track)
    weekdays_with_avg_dist = []

    for k, group in itertools.groupby(used_all, key=get_day_of_week_from_track):
        avg_dist = get_avg_dist_from_group(list(group))
        weekdays_with_avg_dist.append((k, avg_dist))

    objects = [DAYS_OF_WEEK[weekday] for (weekday, avg_d) in weekdays_with_avg_dist]
    y_pos = np.arange(len(objects))
    usage = [usages for (weekday, usages) in weekdays_with_avg_dist]
    plt.barh(y_pos, usage, align='center', alpha=0.5)
    plt.yticks(y_pos, objects)
    plt.xlabel('Average distance [m]')
    plt.show()


def create_bar_chart_for_usage_in_days_of_week(used_all: list):
    calculate_usages_grouped_by_weekday(used_all)


def load_fetched_distances():
    coords_to_distance = {}

    with open('routes2.json', 'r') as fl:
        tracks = list(reduce(operator.concat, list(json.load(fl).values())))
        for track in tracks:
            coords_to_distance[(get_from_coords(track), get_to_coords(track))] = track['distance']

    return coords_to_distance


def add_distance_to_tracks(tracks: dict, coords_to_distances: dict):
    items = tracks.items()
    for i, (_, tracks) in enumerate(items):
        for track in tracks:
            dist = coords_to_distances.get((get_from_coords(track), get_to_coords(track)))
            while dist is None:
                dist = get_walking_distance(track['from'], track['to'])
            track['distance'] = dist
        print('Completion: {:0.2f}'.format((i / len(items)) * 100))


def create_scatter_plot_of_energy_and_distance(tracks: list):
    print('Energy to distance:')
    distances = []
    energies = []
    for track in tracks:
        distances.append(track['distance'])
        energies.append(fuelLevel_diff(track))

    distances = np.array(distances)
    energies = np.array(energies)
    model = LinearRegression().fit(distances.reshape(-1, 1), energies.reshape(-1, 1))
    y_pred = model.predict(distances.reshape(-1, 1))
    covariance = np.cov(distances, energies)
    print('Covariance: \n', covariance)
    corr, _ = stats.spearmanr(distances, energies)
    print('Spearmans correlation: ', corr)
    plt.plot(distances, y_pred, 'r')
    plt.plot(distances, energies, '.')
    plt.xlabel('distance [m]')
    plt.ylabel('energy consumption')
    plt.show()


def create_scatter_plot_of_time_and_distance(tracks: list):
    print('Time to distance:')
    distances = []
    times = []
    for track in tracks:
        distances.append(track['distance'])
        times.append(calculate_duration(track))

    distances = np.array(distances)
    times = np.array(times)
    model = LinearRegression().fit(distances.reshape(-1, 1), times.reshape(-1, 1))
    y_pred = model.predict(distances.reshape(-1, 1))
    covariance = np.cov(distances, times)
    print('Covariance: \n', covariance)
    corr, _ = stats.spearmanr(distances, times)
    print('Spearmans correlation: ', corr)
    plt.plot(distances, y_pred, 'r')
    plt.plot(distances, times, '.')
    plt.xlabel('distance [m]')
    plt.ylabel('time [min]')
    plt.show()


def create_scatter_plot_of_time_and_energy(tracks: list):
    print('Energy to time:')
    energies = []
    times = []
    for track in tracks:
        energies.append(fuelLevel_diff(track))
        times.append(calculate_duration(track))

    energies = np.array(energies)
    times = np.array(times)
    model = LinearRegression().fit(energies.reshape(-1, 1), times.reshape(-1, 1))
    y_pred = model.predict(energies.reshape(-1, 1))
    covariance = np.cov(energies, times)
    print('Covariance: \n', covariance)
    corr, _ = stats.spearmanr(energies, times)
    print('Spearmans correlation: ', corr)
    plt.plot(energies, y_pred, 'r')
    plt.plot(energies, times, '.')
    plt.xlabel('energy')
    plt.ylabel('time [min]')
    plt.show()

# a = NodesFetcher("bolt://192.168.56.102/", "neo4j", "hive")

# # print(calculate_min_max_average_difference_between_scooters_and_pois(
# #     a.get_data_to_check_distance_between_scooters_and_pois()))
# # print(a.get_tracks()[12514])
# filtered, filtered_out = filter_too_long_tracks_for_scooters(a.get_tracks())
# a.close()
# used, charging, in_transport, discharging_and_not_used, teleported = divide_tracks_for_scooters_by_used_and_charging(filtered)
# # min_dist, max_dist, avg = calculate_min_max_avg_track_distance(
# #     random.choices(list(reduce(operator.concat, list(used.values()))), k=100))
# # print(min_dist, max_dist, avg)
#
# # create_bar_chart_with_usage_of_scooters(used)
#
# all_tracks = list(reduce(operator.concat, list(used.values())))
# calculate_usages_grouped_by_weekday(all_tracks)
# # distances = load_fetched_distances()
# # add_distance_to_tracks(used, distances)
# # j = json.dumps(used, indent=4)
# # f = open('routes3.json', 'w')
# # print(j, file=f)
# # f.close()
#
# # j = json.dumps(discharging_and_not_used, indent=4)
# # f = open('discharging.js', 'w')
# # print(j, file=f)
# # f.close()

with open('routes3.json', 'r') as f:
    used = json.load(f)
    # min_dist, max_dist, avg = calculate_min_max_avg_track_distance(list(reduce(operator.concat, list(used.values()))))
    # print(min_dist, max_dist, avg)
    # calculate_avg_distance_grouped_by_weekday(list(reduce(operator.concat, list(used.values()))))
    create_scatter_plot_of_energy_and_distance(list(reduce(operator.concat, list(used.values()))))
    create_scatter_plot_of_time_and_energy(list(reduce(operator.concat, list(used.values()))))
    create_scatter_plot_of_time_and_distance(list(reduce(operator.concat, list(used.values()))))
