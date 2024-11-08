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

    def get_experiment_info_for_user(self, user_id, set_empty_threshold=0.2):
        # set_empty_threshold set the label to empty if the probability value is too small.
        query_experiment_info = f"""
                    MATCH (e:Experiment)-[:SUBMITTED_BY]-(u:User {{user_id: '{user_id}'}})
                    MATCH (e)-[:USED]-(m:Model)
                    MATCH (e)-[:EXECUTED_ON]-(d:EdgeDevice)
                    MATCH (e)-[r:PROCESSED_BY]-(img:RawImage)
                    WITH e.experiment_id AS experimentId, e.start_time AS startTime, 
                         COUNT(img) AS numberOfRawImages, 
                         SUM(CASE WHEN r.image_decision = 'Save' THEN 1 ELSE 0 END) AS numSavedImages, 
                         u.user_id AS userId, m.model_id AS modelId, d.device_id AS deviceId
                    RETURN experimentId, userId, modelId, deviceId, startTime, numberOfRawImages, numSavedImages
                    """

        query_save_accuracy = f"""
                    MATCH (ri:RawImage)-[pb:PROCESSED_BY]->(e:Experiment)-[:SUBMITTED_BY]->(u:User {{user_id: '{user_id}'}})
                    WITH ri, pb, e, apoc.convert.fromJsonList(pb.scores) AS scoresList
                    UNWIND scoresList AS score
                    WITH ri, e, score.label AS label, score.probability AS probability
                    ORDER BY probability DESC
                    WITH ri, e, 
                        CASE WHEN collect(probability)[0] < 0.2 THEN 'empty' ELSE collect(label)[0] END AS predicted_label,
                        CASE WHEN ri.ground_truth IS NULL OR ri.ground_truth = 'unknown' THEN 'empty' ELSE ri.ground_truth END AS ground_truth
                    WITH ri, e, predicted_label, ground_truth, 
                        CASE WHEN ground_truth = predicted_label THEN 1 ELSE 0 END AS accuracy
                    WITH e, avg(accuracy) AS avg_accuracy, collect({{predicted_label: predicted_label, ground_truth: ground_truth}}) AS labels
                    RETURN e.experiment_id AS experimentId, avg_accuracy * 100 AS averageAccuracy
            """

        # get experiment info
        result = self.session.run(query_experiment_info)
        experiment_info_records = [record.data() for record in result]
        df_experiment_info = pd.DataFrame(experiment_info_records)

        # calculate accuracy per experiment
        result = self.session.run(query_save_accuracy)
        save_accuracy_records = [record.data() for record in result]
        df_save_accuracy = pd.DataFrame(save_accuracy_records)

        df_combined = pd.merge(df_experiment_info, df_save_accuracy, on='experimentId')
        print(df_combined)
        # Rename columns as per your requirement
        df_combined.columns = ["Experiment", "User", "Model", "Device", "Start Time", "Total Images", "Saved Images", "Accuracy [%]"]

        # Convert Start Time to datetime
        df_combined['Start Time'] = pd.to_datetime(df_combined['Start Time'], unit='ms')
        # Convert the timezone to EDT
        df_combined['Start Time'] = df_combined['Start Time'].dt.tz_localize('UTC')
        df_combined['Start Time'] = df_combined['Start Time'].dt.tz_convert('America/New_York')

        df_combined.set_index("Experiment", inplace=True)
        return df_combined

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

        try:
            result = self.session.run(query)
            users = [record["user_id"] for record in result]

        except Exception as e:
            print(f"Error fetching users: {e}")
            users = None

        return users

    def fetch_distinct_compiler_applications(self):
        query = """
            MATCH (app:Application)
            RETURN DISTINCT app.name AS application_name
            """

        result = self.session.run(query)
        applications = [record["application_name"] for record in result]

        return applications

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

    def get_exp_deployment_info(self, experiment_id):
        query = """
            MATCH (exp:Experiment {experiment_id: '""" + experiment_id + """'})-[:DEPLOYMENT_INFO]->(d:Deployment)
            RETURN exp.experiment_id as Experiment, d
            """
        result = self.session.run(query)
        records = [record.data() for record in result]

        if records is not None:
            deployments = []
            for record in records:
                deployment_info = record.get("d", {})
                deployment_info.update({
                    "Experiment": record.get("Experiment")
                })
                deployments.append(deployment_info)

            df = pd.DataFrame(deployments)
            if df.empty:
                return None

            df['Start Time'] = pd.to_datetime(df['start_time'], unit='ms')
            # convert time to EDT
            df['Start Time'] = df['Start Time'].dt.tz_localize('UTC')
            df['Start Time'] = df['Start Time'].dt.tz_convert('America/New_York')

            df['End Time'] = pd.to_datetime(df['end_time'], unit='ms')
            # convert time to EDT
            df['End Time'] = df['End Time'].dt.tz_localize('UTC')
            df['End Time'] = df['End Time'].dt.tz_convert('America/New_York')

            return df
        else:
            return None

    def get_all_exp_info(self):
        query = f"""
        MATCH (e:Experiment)-[r:PROCESSED_BY]-(img:RawImage)
        MATCH (e)-[:SUBMITTED_BY]-(u:User)
        MATCH (e)-[:USED]-(m:Model)
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

    def get_device_type(self, experiment_id):
        query = """
        MATCH (n:EdgeDevice)<-[:EXECUTED_ON]-(exp:Experiment {experiment_id: '""" + experiment_id + """'}) RETURN n.device_type as device_type
        """

        result = self.session.run(query)
        device_type = result.single()["device_type"]
        return device_type

    def get_exp_info_raw(self, experiment_id):
        query = """
        MATCH (e:Experiment {experiment_id: '""" + experiment_id + """'})-[r:PROCESSED_BY]-(img:RawImage)
        RETURN {
            image_name: img.image_name,
            ground_truth: img.ground_truth, 
            image_scoring_timestamp: r.image_scoring_timestamp, 
            model_id: r.model_id, 
            ingestion_timestamp: r.ingestion_timestamp, 
            image_store_delete_time: r.image_store_delete_time, 
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
            "image_decision",
            "scores"
        ])

        # Convert Neo4j DateTime objects to Python datetime objects
        date_columns = ["image_scoring_timestamp", "image_store_delete_time", "ingestion_timestamp"]
        for col in date_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.convert_to_native)

        df.columns = ["Image", "Ground Truth", "Score Time", "Ingestion Time", "Delete Time", "Model",
                      "Decision", "Scores"]
        df.set_index("Ingestion Time", inplace=True)
        return df

    def fetch_experiments(self, user_id):
        query = f"""
        MATCH (u:User {{user_id: '{user_id}' }})<-[:SUBMITTED_BY]-(e:Experiment)-[:EXECUTED_ON]->(d:EdgeDevice),
      (e)-[:USED]->(m:Model)
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

    def fetch_profile_runs(self, application_name):
        query = f"""
            MATCH (app:Application {{name: '{application_name}' }})-[data:PROFILED_BY]->(prof:Profiling) 
            RETURN DISTINCT prof.uuid as profile_run
            """
        result = self.session.run(query)
        records = result.data()
        df = pd.DataFrame(records)
        return df

    def fetch_profile_run_info(self, profile_id):
        query = f"""
            MATCH (app:Application)-[rel:PROFILED_BY]->(opt:Profiling {{uuid: '{profile_id}' }}) 
            RETURN 
            rel.loop_id AS loop_id,
              rel.DataSize AS DataSize,
              rel.Number_of_Iterations AS Number_of_Iterations,
              rel.total_of_Iterations AS total_of_Iterations,
              rel.Number_of_Loads AS Number_of_Loads,
              rel.Number_of_Stores AS Number_of_Stores,
              rel.Number_of_Instructions AS Number_of_Instructions,
              rel.Number_of_Statements AS Number_of_Statements,
              rel.Loopness_Level AS Loopness_Level,
              rel.No_of_Bits_per_iteration AS No_of_Bits_per_iteration,
              rel.No_of_Times_a_Data_Type_Changed AS No_of_Times_a_Data_Type_Changed,
              rel.No_of_Integer_Operation_Type AS No_of_Integer_Operation_Type,
              rel.No_of_Float_Operation_Type AS No_of_Float_Operation_Type,
              rel.No_of_Double_Operation_Type AS No_of_Double_Operation_Type,
              rel.No_of_Long_Double_Operation AS No_of_Long_Double_Operation,
              rel.No_of_Long_Operation AS No_of_Long_Operation,
              rel.No_of_Short_Operation AS No_of_Short_Operation,
              rel.Big_O_Notation AS Big_O_Notation,
              rel.No_of_multiplication AS No_of_multiplication,
              rel.No_of_substraction AS No_of_substraction,
              rel.No_of_addition AS No_of_addition,
              rel.No_of_Function_Calls_Side_effect_Free AS No_of_Function_Calls_Side_effect_Free,
              rel.Data_dependence_Free AS Data_dependence_Free,
              rel.Ratio_of_Reduction_Statements AS Ratio_of_Reduction_Statements,
              rel.Ratio_of_Flow_Dependences_Remaining AS Ratio_of_Flow_Dependences_Remaining
            """
        result = self.session.run(query)
        records = result.data()
        df = pd.DataFrame(records)
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
        OPTIONAL MATCH (e)-[ub:USED]->(m:Model)
        OPTIONAL MATCH (ri:RawImage)-[pb:PROCESSED_BY]->(e)
        RETURN e, 
            collect(DISTINCT {user: u, submitted_time: sb.submitted_time}) AS submitted_by,
            collect(DISTINCT {edge_device: ed, executed_time: eo.submitted_time}) AS executed_on,
            collect(DISTINCT {model: m, used_start_time: ub.start_time}) AS used,
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
        try:
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

        except Exception as e:
            print(f"Error fetching alerts: {e}")
            return pd.DataFrame()

    def get_result_query(self, query, parameters):
        with self.driver.session() as session:
            result = session.run(query, parameters).single()
        return result

    def get_mode_name_version(self, model_id):
        """
            Get model information.
        """
        query = """
            MATCH (m:Model {model_id: '""" + model_id + """'}) 
            RETURN m.name + ':' + m.version AS name_version
        """
        result = self.session.run(query)
        name_version = result.single()["name_version"]

        # Returning the 'name:version' string
        return name_version

    def get_model_card_ids(self):
        """
        Get all the model card IDs
        :return:
        """
        query = """
             MATCH (mc:ModelCard)
             RETURN mc.external_id as model_card_id
             """
        result = self.session.run(query)
        records = [record["model_card_id"] for record in result]

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records, columns=['Model Card ID'])
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
