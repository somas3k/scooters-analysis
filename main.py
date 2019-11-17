from neo4j import GraphDatabase
import math


class NodesFetcher(object):

    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def get_data_to_check_distance_between_scooters_and_pois(self):
        with self._driver.session() as session:
            return session.write_transaction(self._get_data_to_check_distance_between_scooters_and_pois).values()

    def get_scooters(self):
        with self._driver.session() as session:
            return session.write_transaction(self._get_scooters).single()

    def get_tracks(self):
        with self._driver.session() as session:
            return session.write_transaction(self._get_tracks)

    @staticmethod
    def _get_ordered_stays_at_locations(tx, scooter_id):
        return

    @staticmethod
    def _get_data_to_check_distance_between_scooters_and_pois(tx):
        return tx.run("MATCH ()-[t:STAYS_AT]->(l:Location) "
                      "RETURN t.exactLat, t.exactLon, l.lat, l.lng "
                      "ORDER BY t.from")

    @staticmethod
    def _get_scooters(tx):
        return tx.run("MATCH (n:Scooter)-[t:STAYS_AT]->(l:Location) "
                      "RETURN n, t, l "
                      "ORDER BY t.from")


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


a = NodesFetcher("bolt://192.168.56.102", "neo4j", "hive")

print(calculate_min_max_average_difference_between_scooters_and_pois(a.get_data_to_check_distance_between_scooters_and_pois()))
a.close()