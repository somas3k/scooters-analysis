from neo4j import GraphDatabase


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
            return session.write_transaction(self._get_scooters).value()

    def get_tracks(self):
        scooters = self.get_scooters()
        scooter_to_tracks = {}

        for scooter in scooters:
            with self._driver.session() as session:
                stays_at_location = \
                    session.write_transaction(self._get_ordered_stays_at_locations, scooter["carId"]).data()
                prev = None
                tracks = []
                for st in stays_at_location:
                    if prev:
                        tracks.append({"from": prev, "to": st})
                    prev = st
                scooter_to_tracks[scooter["carId"]] = tracks

        return scooter_to_tracks

    @staticmethod
    def _get_ordered_stays_at_locations(tx, scooter_id):
        return tx.run("match (n:Scooter)-[t:STAYS_AT]->(l:Location) "
                      "where n.carId=$scooter_id "
                      "return properties(t) as stays_at, properties(l) as location order by t.from",
                      scooter_id=scooter_id)

    @staticmethod
    def _get_data_to_check_distance_between_scooters_and_pois(tx):
        return tx.run("MATCH ()-[t:STAYS_AT]->(l:Location) "
                      "RETURN t.exactLat, t.exactLon, l.lat, l.lng "
                      "ORDER BY t.from")

    @staticmethod
    def _get_scooters(tx):
        return tx.run("MATCH (n:Scooter) "
                      "RETURN properties(n)")
