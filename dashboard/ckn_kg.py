from datetime import datetime
from neo4j import GraphDatabase
import pandas as pd


class CKNKnowledgeGraph():

    def __init__(self, ckn_uri, ckn_user, ckn_pwd):
        self.driver = GraphDatabase.driver(ckn_uri, auth=(ckn_user, ckn_pwd))
        self.session = self.driver.session()

    def close(self):
        self.session.close()

    def get_statistics(self):
        queries = {
            "average_probability":
            """
                MATCH (u:User)-[r:SUBMITTED_BY]-(e:Experiment)-[p:PROCESSED_BY]-(i:RawImage)
                WITH p, apoc.convert.fromJsonList(p.scores) AS scores
                UNWIND scores AS score
                WITH p, MAX(toFloat(score.probability)) AS max_probability
                RETURN avg(max_probability) AS value
            """,
            "user_count":
            """
                MATCH (u:User)
                RETURN count(u) AS value
            """,
            "image_count":
            """
                MATCH (i:RawImage)
                RETURN count(i) AS value
            """,
            "device_count":
            """
                MATCH (d:EdgeDevice)
                RETURN count(d) AS value
            """
        }
        results = {}
        with self.session.begin_transaction() as tx:
            for key, query in queries.items():
                result = tx.run(query).single()
                results[key] = result["value"] if result else 0
        return results

    def get_experiment_info(self):
        query = """
        MATCH (e:Experiment {experiment_id: "tapis-exp5-3442334"})
        OPTIONAL MATCH (e)-[sb:SUBMITTED_BY]->(u:User)
        OPTIONAL MATCH (e)-[eo:EXECUTED_ON]->(ed:EdgeDevice)
        OPTIONAL MATCH (e)-[ub:USED_BY]->(m:Model)
        OPTIONAL MATCH (ri:RawImage)-[pb:PROCESSED_BY]->(e)
        RETURN e, 
            collect(DISTINCT {user: u, submitted_time: sb.submitted_time}) AS submitted_by,
            collect(DISTINCT {edge_device: ed, executed_time: eo.submitted_time}) AS executed_on,
            collect(DISTINCT {model: m, used_start_time: ub.start_time}) AS used_by,
            collect(DISTINCT {raw_image: ri, processed_by: pb}) AS processed_images"""

        result = self.session.run(query)
        return [record.data() for record in result]

    def fetch_accuracy_trend(self, date_range, image_saved=True):
        start_date, end_date = date_range
        decision_clause = "AND pb.image_decision = 'Save'" if image_saved else ""
        query = f"""
        MATCH (ri:RawImage)-[pb:PROCESSED_BY]-(e:Experiment)
        WHERE pb.image_scoring_timestamp >= datetime("{start_date.isoformat()}") AND pb.image_scoring_timestamp <= datetime("{end_date.isoformat()}")
        {decision_clause}
        WITH pb, pb.image_scoring_timestamp AS image_scoring_timestamp, apoc.convert.fromJsonList(pb.scores) AS scores
        UNWIND scores AS score
        RETURN pb.image_scoring_timestamp AS image_scoring_timestamp, score.probability AS probability
        """

        result = self.session.run(query)
        records = [
            (self.convert_to_datetime(record["image_scoring_timestamp"]),
             record["probability"]) for record in result
        ]

        df = pd.DataFrame(records,
                          columns=["image_scoring_timestamp", "probability"])
        df = df.sort_values(by='image_scoring_timestamp')

        return df

    def fetch_distinct_users(self):
        query = """
        MATCH (u:User)
        RETURN DISTINCT u.user_id AS user_id
        """

        result = self.session.run(query)
        users = [record["user_id"] for record in result]

        return users

    def fetch_distinct_devices(self):
        query = """
        MATCH (d:EdgeDevice)
        RETURN DISTINCT d.device_id AS device_id
        """

        result = self.session.run(query)
        devices = [record["device_id"] for record in result]

        return devices

    def fetch_distinct_experiment_id(self):
        query = """
        MATCH (e:Experiment)
        RETURN DISTINCT e.experiment_id AS experiment_id
        """

        result = self.session.run(query)
        experiment_ids = [record["experiment_id"] for record in result]

        return experiment_ids

    def fetch_latest_served_by_edges(self, limit=100):
        query = """
        MATCH (e:Experiment {experiment_id: "tapis-exp5-3442334"})
        OPTIONAL MATCH (e)-[sb:SUBMITTED_BY]->(u:User)
        OPTIONAL MATCH (e)-[eo:EXECUTED_ON]->(ed:EdgeDevice)
        OPTIONAL MATCH (e)-[ub:USED_BY]->(m:Model)
        OPTIONAL MATCH (ri:RawImage)-[pb:PROCESSED_BY]->(e)
        RETURN e, 
            collect(DISTINCT {user: u, submitted_time: sb.submitted_time}) AS submitted_by,
            collect(DISTINCT {edge_device: ed, executed_time: eo.submitted_time}) AS executed_on,
            collect(DISTINCT {model: m, used_start_time: ub.start_time}) AS used_by,
            collect(DISTINCT {raw_image: ri, processed_by: pb}) AS processed_images
        LIMIT $limit
        """
        result = self.session.run(query, limit=limit)
        return [record.data() for record in result]

    def fetch_alerts(self, limit=100):
        query = """
            MATCH (alert:ALERT)
            RETURN alert
            ORDER BY alert.timestamp DESC
            LIMIT $limit
            """
        result = self.session.run(query, limit=limit)
        records = [record["alert"] for record in result]

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df['timestamp'] = df['timestamp'].apply(self.convert_to_datetime)
        df = df[[
            'timestamp', 'alert_name', 'priority', 'source_topic',
            'description', 'UUID', 'event_data'
        ]]
        df.set_index('timestamp', inplace=True)

        return df

    def convert_to_datetime(self, neo4j_datetime):
        return datetime(neo4j_datetime.year,
                        neo4j_datetime.month,
                        neo4j_datetime.day,
                        neo4j_datetime.hour,
                        neo4j_datetime.minute,
                        int(neo4j_datetime.second),
                        int(neo4j_datetime.nanosecond / 1000),
                        tzinfo=neo4j_datetime.tzinfo)
