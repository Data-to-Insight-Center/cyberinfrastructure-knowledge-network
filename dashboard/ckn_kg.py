from datetime import datetime
from neo4j import GraphDatabase
import neo4j
import pandas as pd


class CKNKnowledgeGraph:

    def __init__(self, ckn_uri, ckn_user, ckn_pwd):
        self.driver = GraphDatabase.driver(ckn_uri, auth=(ckn_user, ckn_pwd))
        self.session = self.driver.session()

    def close(self):
        self.session.close()

    def get_statistics(self,
                       experiment_ids=None,
                       device_ids=None,
                       user_ids=None,
                       date_range=None,
                       image_decision='Saved'):

        def generate_clause(clause_type, values):
            if values:
                return f"{clause_type} IN {values}"
            return "true"  # Always true if no values are provided

        date_range_clause = (
            f"p.image_scoring_timestamp >= datetime('{date_range[0].isoformat()}') "
            f"AND p.image_scoring_timestamp <= datetime('{date_range[1].isoformat()}')"
            if date_range else "true")
        experiment_clause = generate_clause("e.experiment_id", experiment_ids)
        device_clause = generate_clause("d.device_id", device_ids)
        user_clause = generate_clause("u.user_id", user_ids)

        queries = {
            "average_probability":
                f"""
                MATCH (u:User)-[r:SUBMITTED_BY]-(e:Experiment)-[p:PROCESSED_BY]-(i:RawImage)
                WITH p, apoc.convert.fromJsonList(p.scores) AS scores
                UNWIND scores AS score
                WITH p, MAX(toFloat(score.probability)) AS max_probability
                WHERE {date_range_clause} AND {experiment_clause} AND {device_clause} AND {user_clause}
                RETURN round(avg(max_probability)*100) AS value
                """,
            "user_count":
                f"""
                MATCH (u:User)
                WHERE {date_range_clause} AND {experiment_clause} AND {device_clause} AND {user_clause}
                RETURN count(u) AS value
            """,
            "image_count":
                f"""
                MATCH (i:RawImage)-[p:PROCESSED_BY]->(e:Experiment)-[:EXECUTED_ON]->(d:EdgeDevice)
                WHERE {date_range_clause} AND {experiment_clause} AND {device_clause} AND {user_clause}
                RETURN count(DISTINCT i) AS value
            """,
            "device_count":
                f"""
                MATCH (d:EdgeDevice)-[:EXECUTED_ON]->(e:Experiment)-[p:PROCESSED_BY]->(i:RawImage)
                WHERE {date_range_clause} AND {experiment_clause} AND {device_clause} AND {user_clause}
                RETURN count(DISTINCT d) AS value
            """
        }

        results = {}
        with self.session.begin_transaction() as tx:
            for key, query in queries.items():
                final_query = query
                result = tx.run(final_query,
                                image_decision=image_decision).single()
                results[key] = result["value"] if result else 0
        return results

    def get_experiment_info_for_user(self, user_id):
        query = f"""
                MATCH (e:Experiment)-[r:PROCESSED_BY]-(img:RawImage)
                MATCH (e)-[:SUBMITTED_BY]-(u:User {{user_id: '{user_id}'}})
                MATCH (e)-[:USED_BY]-(m:Model)
                MATCH (e)-[:EXECUTED_ON]-(d:EdgeDevice)
                WITH e.experiment_id AS experimentId, e.start_time AS startTime, COUNT(img) AS NumberOfRawImages, COLLECT(r) AS relationships, u.user_id AS userId, m.model_id AS modelId, d.device_id AS deviceId
                UNWIND relationships AS r
                WITH experimentId, startTime, NumberOfRawImages, COUNT(CASE WHEN r.image_decision = 'Save' THEN 1 END) AS NumberOfSavedImages, relationships, userId, modelId, deviceId
                UNWIND relationships AS r
                WITH experimentId, startTime, NumberOfRawImages, NumberOfSavedImages, userId, modelId, deviceId, r
                WHERE r.image_decision = 'Save'
                WITH experimentId, startTime, NumberOfRawImages, NumberOfSavedImages, userId, modelId, deviceId, apoc.convert.fromJsonList(r.scores) AS scores
                UNWIND scores AS score
                WITH experimentId, startTime, NumberOfRawImages, NumberOfSavedImages, userId, modelId, deviceId, toFloat(score.probability) AS probability
                RETURN experimentId, userId, modelId, deviceId, AVG(probability)*100 AS average_accuracy, startTime, NumberOfRawImages, NumberOfSavedImages
                """

        result = self.session.run(query)

        records = [record.data() for record in result]
        df = pd.DataFrame(records)
        df.columns = ["Experiment", "User", "Model", "Device", "Accuracy [%]", "Start Time", "Total Images",
                      "Saved Images"]
        df['Start Time'] = pd.to_datetime(df['Start Time'], unit='ms')  # Convert to datetime
        df.set_index("Experiment", inplace=True)  # Set experiment_id as the index
        return df

    def fetch_accuracy_trend(self, date_range, experiment_id, image_saved=True):
        start_date, end_date = date_range
        decision_clause = "AND pb.image_decision = 'Save'" if image_saved else ""
        query = f"""
        MATCH (ri:RawImage)-[pb:PROCESSED_BY]-(e:Experiment {{experiment_id: '{experiment_id}'}})
        WHERE pb.image_scoring_timestamp >= datetime("{start_date.isoformat()}") AND pb.image_scoring_timestamp <= datetime("{end_date.isoformat()}")
        {decision_clause}
        WITH pb, pb.image_scoring_timestamp AS image_scoring_timestamp, apoc.convert.fromJsonList(pb.scores) AS scores
        UNWIND scores AS score
        RETURN pb.image_scoring_timestamp AS image_scoring_timestamp, score.probability AS probability
        """

        result = self.session.run(query)
        records = [
            (self.convert_to_datetime(record["image_scoring_timestamp"]), record["probability"])
            for record in result
        ]

        df = pd.DataFrame(records, columns=["image_scoring_timestamp", "probability"])
        df = df.sort_values(by='image_scoring_timestamp')

        return df

    def fetch_accuracy_for_experiment(self, experiment_id):
        query = f"""
        MATCH (ri:RawImage)-[pb:PROCESSED_BY]-(e:Experiment {{experiment_id: '{experiment_id}'}})
        WHERE pb.image_decision = 'Save'
        WITH pb, pb.image_scoring_timestamp AS image_scoring_timestamp, apoc.convert.fromJsonList(pb.scores) AS scores
        UNWIND scores AS score
        RETURN pb.image_scoring_timestamp AS image_scoring_timestamp, score.probability AS probability
        """

        result = self.session.run(query)
        records = [
            (self.convert_to_datetime(record["image_scoring_timestamp"]), record["probability"])
            for record in result
        ]

        df = pd.DataFrame(records, columns=["Timestamp", "Accuracy"])
        df = df.sort_values(by='Timestamp')

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

    def get_all_exp_info(self):
        query = f"""
        MATCH (e:Experiment)-[r:PROCESSED_BY]-(img:RawImage)
        MATCH (e)-[:SUBMITTED_BY]-(u:User)
        MATCH (e)-[:USED_BY]-(m:Model)
        MATCH (e)-[:EXECUTED_ON]-(d:EdgeDevice)
        WITH e.experiment_id AS experimentId, e.start_time AS startTime, COUNT(img) AS NumberOfRawImages, COLLECT(r) AS relationships, u.user_id AS userId, m.model_id AS modelId, d.device_id AS deviceId
        UNWIND relationships AS r
        WITH experimentId, startTime, NumberOfRawImages, COUNT(CASE WHEN r.image_decision = 'Save' THEN 1 END) AS NumberOfSavedImages, relationships, userId, modelId, deviceId
        UNWIND relationships AS r
        WITH experimentId, startTime, NumberOfRawImages, NumberOfSavedImages, userId, modelId, deviceId, apoc.convert.fromJsonList(r.scores) AS scores
        UNWIND scores AS score
        WITH experimentId, startTime, NumberOfRawImages, NumberOfSavedImages, userId, modelId, deviceId, toFloat(score.probability) AS probability
        RETURN experimentId, userId, modelId, deviceId, AVG(probability)*100 AS average_accuracy, startTime, NumberOfRawImages, NumberOfSavedImages
        """

        result = self.session.run(query)

        records = [record.data() for record in result]
        df = pd.DataFrame(records)
        df.columns = ["Experiment", "User", "Model", "Device", "Accuracy [%]", "Start Time", "Total Images",
                      "Saved Images"]
        df['Start Time'] = pd.to_datetime(df['Start Time'], unit='ms')  # Convert to datetime
        df.set_index("Experiment", inplace=True)  # Set experiment_id as the index
        return df

    def get_exp_info_raw(self, experiment_id):
        query = """
        MATCH (e:Experiment {experiment_id: '""" + experiment_id + """'})-[r:PROCESSED_BY]-(img:RawImage)
        RETURN {
            image_name: img.image_name,
            ground_truth: img.ground_truth, 
            image_scoring_timestamp: r.image_scoring_timestamp, 
            ingestion_timestamp: r.ingestion_timestamp, 
            image_store_delete_time: r.image_store_delete_time, 
            model_id: r.model_id, 
            image_count: r.image_count, 
            image_decision: r.image_decision, 
            scores: r.scores
        } AS processed_by_detail
        """
        result = self.session.run(query)
        records = [record["processed_by_detail"] for record in result]

        df = pd.DataFrame(records, columns=[
            "image_name",
            "ground_truth",
            "image_scoring_timestamp",
            "ingestion_timestamp",
            "image_store_delete_time",
            "model_id",
            "image_count",
            "image_decision",
            "scores"
        ])

        # Convert Neo4j DateTime objects to Python datetime objects
        date_columns = ["image_scoring_timestamp", "image_store_delete_time", "ingestion_timestamp"]
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.convert_to_native)

        df.columns = ["Image", "Ground Truth", "Score Time", "Ingestion Time", "Delete Time", "Model", "Images",
                      "Decision", "Scores"]
        df.set_index("Score Time", inplace=True)
        return df

    def fetch_experiments(self, user_id):
        query = f"""
        MATCH (u:User {{user_id: '{user_id}' }})<-[:SUBMITTED_BY]-(e:Experiment)-[:EXECUTED_ON]->(d:EdgeDevice),
      (e)-[:USED_BY]->(m:Model)
        RETURN e.experiment_id AS experiment_id,
       e.start_time AS timestamp,
       d.device_id AS device_id,
       m.model_id AS model_id
        """
        result = self.session.run(query)
        records = result.data()
        df = pd.DataFrame(records)
        df = df[['experiment_id', 'timestamp', 'device_id', 'model_id']]
        df.set_index('timestamp', inplace=True)
        return df

    def get_user_info(self, user_id):
        query = """
        MATCH (u:User {user_id: '""" + user_id + """'})-[:SUBMITTED_BY]-(e:Experiment)-[r:PROCESSED_BY]-(img:RawImage)
        MATCH (e)-[:EXECUTED_ON]-(d:EdgeDevice)
        WITH e, d, e.experiment_id AS exp_id, e.start_time AS timestamp, d.device_id AS device_id, apoc.convert.fromJsonList(r.scores) AS scores
        UNWIND scores AS score
        WITH e, d, exp_id, timestamp, device_id, toFloat(score.probability) AS probability
        RETURN timestamp, exp_id, device_id, AVG(probability) AS average_probability
        """

        result = self.session.run(query)
        records = result.data()
        df = pd.DataFrame(records)
        df = df[['timestamp', 'exp_id', 'device_id', 'average_accuracy']]
        df.set_index('timestamp', inplace=True)

        return df

    def experiment_info(self, user_id):
        query = """
        MATCH (u:User {user_id: '""" + user_id + """'})-[:SUBMITTED_BY]-(e:Experiment)-[r:PROCESSED_BY {image_decision: 'Save'}]-(img:RawImage)
        MATCH (e)-[:EXECUTED_ON]-(d:EdgeDevice)
        WITH e, d, r, e.experiment_id AS exp_id, e.start_time AS timestamp, d.device_id AS device_id, apoc.convert.fromJsonList(r.scores) AS scores
        UNWIND scores AS score
        WITH e, d, r, exp_id, timestamp, device_id, toFloat(score.probability) AS probability
        RETURN timestamp, exp_id, device_id, AVG(probability) AS average_probability, r.image_decision AS image_decision
        """

        result = self.session.run(query)
        records = result.data()
        df = pd.DataFrame(records)
        df = df[['timestamp', 'exp_id', 'device_id', 'average_probability']]
        df.columns = ['Timestamp', 'Experiment ID', 'Device ID', 'Average Accuracy']
        df.set_index('Timestamp', inplace=True)

        return df

    def get_device_info(self, device_id):
        query = """
        MATCH (d:EdgeDevice {device_id: '""" + device_id + """'})-[:EXECUTED_ON]-(e:Experiment)-[:SUBMITTED_BY]-(u:User)
        MATCH (e)-[r:PROCESSED_BY]-(img:RawImage)
        WITH e, u, e.experiment_id AS exp_id, e.start_time AS timestamp, u.user_id AS user_id, apoc.convert.fromJsonList(r.scores) AS scores
        UNWIND scores AS score
        WITH e, u, exp_id, timestamp, user_id, toFloat(score.probability) AS probability
        RETURN timestamp, user_id, exp_id, AVG(probability) AS average_accuracy
        """

        result = self.session.run(query)
        records = result.data()

        df = pd.DataFrame(records)
        return df

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
        df.columns = ['Timestamp', 'Alert Name', 'Priority', 'Source Topic', 'Description', 'UUID', 'Event Data']
        df.set_index('Timestamp', inplace=True)
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

    def convert_to_native(self, dt):
        """Convert Neo4j DateTime to Python native datetime"""
        if isinstance(dt, neo4j.time.DateTime):
            return dt.to_native()
        return dt
