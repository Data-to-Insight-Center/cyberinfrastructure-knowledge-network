from datetime import datetime

from neo4j import GraphDatabase
import pandas as pd


class CKNKnowledgeGraph():
    def __init__(self, ckn_uri, ckn_user, ckn_pwd):
        self.driver = GraphDatabase.driver(ckn_uri, auth=(ckn_user, ckn_pwd))

    def fetch_latest_served_by_edges(self, limit=100):
        query = f"""
        MATCH (ri:RawImage)-[r:SERVED_BY]->(es:EdgeServer)
        RETURN
          r.image_count AS image_count,
          r.image_receiving_timestamp AS image_receiving_timestamp,
          r.image_scoring_timestamp AS image_scoring_timestamp,
          r.model_id AS model_id,
          r.scores AS scores,
          r.image_store_delete_time AS image_store_delete_time,
          r.image_decision AS image_decision,
          r.ingestion_timestamp AS ingestion_timestamp,
          ri.UUID AS UUID,
          es.device_id AS device_id
        ORDER BY r.ingestion_timestamp DESC
        LIMIT {limit}
        """

        with self.driver.session() as session:
            result = session.run(query)
            records = [record.data() for record in result]

        return records

    def fetch_alerts(self, limit=100):
        query = f"""
            MATCH (alert:ALERT)
            RETURN alert
            ORDER BY alert.timestamp DESC
            LIMIT {limit}
            """
        with self.driver.session() as session:
            result = session.run(query)
            records = [record["alert"] for record in result]

        alerts = []
        for record in records:
            alert_data = {key: record[key] for key in record.keys()}
            alerts.append(alert_data)

        if len(alerts) < 1:
            return pd.DataFrame()

        df = pd.DataFrame(alerts)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        return df

    def convert_to_datetime(self, neo4j_datetime):
        return datetime(
            neo4j_datetime.year, neo4j_datetime.month, neo4j_datetime.day,
            neo4j_datetime.hour, neo4j_datetime.minute, int(neo4j_datetime.second),
            int(neo4j_datetime.nanosecond / 1000), tzinfo=neo4j_datetime.tzinfo
        )



