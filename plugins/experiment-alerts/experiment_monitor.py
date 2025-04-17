import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
import json
from apscheduler.schedulers.blocking import BlockingScheduler
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, Neo4jError
from kafka import KafkaProducer
from kafka.errors import KafkaError
import redis
from redis import ConnectionPool
from redis.exceptions import RedisError
from dotenv import load_dotenv
from cypher_queries import *

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
# Logging config
logger = logging.getLogger(__name__)

# Redis config
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_ALERTED_SET_KEY = os.getenv('REDIS_ALERTED_SET_KEY', 'experiment_monitor:alerted_experiments')
# setting alerts to be refreshed every 7 days. But this can be configured.
REDIS_ALERTED_TTL_SECONDS = int(os.getenv('REDIS_ALERTED_TTL_SECONDS', 60 * 60 * 24 * 7)) # Keep alerted IDs for 7 days

redis_pool = ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    max_connections=10,
    decode_responses=True
)

# Neo4j config
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'PWD_HERE')

# Kafka config
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'cameratraps-accuracy-alerts')
KAFKA_CLIENT_ID = os.getenv('KAFKA_CLIENT_ID', 'experiment-accuracy-monitor')

# Thresholds
ACCURACY_THRESHOLD = float(os.getenv('ACCURACY_THRESHOLD', 80.0))
ALERT_BATCH_SIZE = float(os.getenv('ALERT_BATCH_SIZE', 500))
PREDICTION_CONFIDENCE_THRESHOLD = float(os.getenv('PREDICTION_CONFIDENCE_THRESHOLD', 0.2)) # For accuracy calc
# Number of days back to check alerts experiments for
HISTORICAL_ALERT_CHECK_RANGE = int(os.getenv('HISTORICAL_ALERT_CHECK_RANGE', 1))

# Scheduling (How often to run the functions below
SCHEDULE_IN_MIN = int(os.getenv('SCHEDULE_IN_MIN', 1))

# Init
def get_redis_connection():
    try:
        return redis.Redis(connection_pool=redis_pool)
    except RedisError as e:
        logger.error(f"Failed to get Redis connection: {e}")
        raise

def initialize_neo4j_driver():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        logger.info("Neo4j connection successful.")
        return driver
    except ServiceUnavailable as e:
        logger.error(f"Failed to connect to Neo4j at {NEO4J_URI}: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during Neo4j initialization: {e}")
        raise

def initialize_kafka_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            client_id=KAFKA_CLIENT_ID,
            acks='all',
            retries=3,
            retry_backoff_ms=100
        )
        logger.info(f"Kafka producer connected to {KAFKA_BOOTSTRAP_SERVERS}")
        return producer
    except KafkaError as e:
        logger.error(f"Failed to initialize Kafka producer: {e}")
        raise

# --- Global Resources ---
redis_conn = None
neo4j_driver = None
kafka_producer = None


def process_completed_experiments():
    """
    Finds experiments associated with finished deployments,
    calculates their duration and accuracy, and updates the experiment node.
    """
    if not neo4j_driver:
        logger.error("Neo4j driver not available. Skipping completion processing.")
        return

    logger.info("Starting processing of completed experiments...")
    processed_count = 0
    try:
        with neo4j_driver.session(database="neo4j") as session:
            # Find experiments that has completed but has not been processed.
            completable_results = session.run(CYPHER_FIND_COMPLETABLE_EXPERIMENTS)
            completable_experiments = [record.data() for record in completable_results]

            if not completable_experiments:
                logger.info("No newly completed experiments found to process.")
                return

            logger.info(f"Found {len(completable_experiments)} experiments to process for completion.")

            # For each experiment, calculate the duration and accuracy
            for exp_data in completable_experiments:
                exp_id = exp_data.get('experiment_id')
                start_time_ms = exp_data.get('start_time_ms')
                end_time_ms = exp_data.get('end_time_ms')

                if not all([exp_id, start_time_ms, end_time_ms]):
                     logger.warning(f"Skipping experiment due to missing data: {exp_data}")
                     continue

                try:
                    # Use an explicit transaction for accuracy calculation + update
                    with session.begin_transaction() as tx:
                        # Calculate Accuracy
                        accuracy_result = tx.run(
                            CYPHER_CALCULATE_ACCURACY,
                            experiment_id=exp_id,
                            confidence_threshold=PREDICTION_CONFIDENCE_THRESHOLD
                        )
                        accuracy_record = accuracy_result.single()

                        if accuracy_record and 'averageAccuracy' in accuracy_record.keys():
                            raw_accuracy = accuracy_record['averageAccuracy']
                            accuracy = round(raw_accuracy, 2)
                            logger.info(f"Calculated accuracy for experiment {exp_id}: {accuracy:.2f}%")
                        else:
                            # Handle cases where accuracy cannot be calculated (e.g., no processed images)
                            accuracy = 0.0
                            logger.warning(f"Could not calculate accuracy for experiment {exp_id}. Setting accuracy to {accuracy}.")

                        # Update Experiment Node
                        update_result = tx.run(
                            CYPHER_UPDATE_COMPLETED_EXPERIMENT,
                            experiment_id=exp_id,
                            start_time_ms=start_time_ms,
                            end_time_ms=end_time_ms,
                            accuracy=accuracy
                        )
                        update_summary = update_result.consume()
                        logger.info(f"Updated experiment {exp_id} with end_time, duration, and accuracy ({update_summary.counters.properties_set} properties set).")
                        processed_count += 1

                except Neo4jError as e:
                     logger.error(f"Neo4j error processing experiment {exp_id}: {e}. Skipping this experiment.")
                except Exception as e:
                     logger.error(f"Unexpected error processing experiment {exp_id}: {e}", exc_info=True)

    except ServiceUnavailable as e:
        logger.error(f"Neo4j connection error during completion processing: {e}")
    except Exception as e:
        logger.error(f"Failed during completion processing: {str(e)}", exc_info=True)

    logger.info(f"Completed experiment processing. Updated {processed_count} experiments.")


def create_low_accuracy_kafka_event(experiment_id, accuracy, model_id, metadata):
    """
    Creates a structured Kafka event dictionary for a low accuracy alert.

    Args:
        experiment_id: The ID of the experiment.
        accuracy: The calculated accuracy (percentage, float or None).
        model_id: The ID of the model used (string or None).
        metadata: The metadata associated with the experiment (dict or None).
                   Assumes temporal types within metadata are already serializable.

    Returns:
        A dictionary formatted for the Kafka alert event.
    """

    # Format accuracy for the human-readable description string
    accuracy_desc = "N/A"
    if isinstance(accuracy, (int, float)):
        accuracy_desc = f"{accuracy:.2f}%"
    elif accuracy is not None:
        accuracy_desc = str(accuracy)

    # Generate timestamp and UUID for the event
    alert_timestamp = datetime.now(timezone.utc).isoformat()
    alert_uuid = f"exp-hist-alert-{uuid.uuid4()}"
    alert_description = f"Experiment {experiment_id} completed with low accuracy: {accuracy_desc}"

    # Create the original event data payload
    original_event_data = {
        'experiment_id': experiment_id,
        'accuracy': accuracy,
        'model_id': model_id,
        # 'metadata': metadata
    }

    # Construct the final Kafka message
    kafka_alert_message = {
        'timestamp': alert_timestamp,
        'alert_name': 'Low Experiment Accuracy',
        'priority': 'HIGH',
        'description': alert_description,
        'UUID': alert_uuid,
        'event_data': original_event_data
    }
    return kafka_alert_message


def check_low_accuracy_alerts():
    """
    Check for experiments completed within the last HISTORICAL_ALERT_CHECK_RANGE days that have
    accuracy below threshold and haven't been alerted yet.
    """
    if not all([redis_conn, neo4j_driver, kafka_producer]):
        logger.error("Required connections not available. Skipping low accuracy alert check.")
        return

    logger.info(f"Starting low accuracy alert check for experiments completed in the last {HISTORICAL_ALERT_CHECK_RANGE} days...")

    # Calculate the time threshold
    try:
        historical_time_delta = datetime.now(timezone.utc) - timedelta(days=HISTORICAL_ALERT_CHECK_RANGE)
        historical_time_delta_iso = historical_time_delta.isoformat()
        logger.debug(f"Checking for experiments completed since: {historical_time_delta_iso}")
    except Exception as e:
        logger.error(f"Error calculating time threshold: {e}", exc_info=True)
        return

    # Find experiments completed recently with low accuracy
    experiments_to_alert = []
    try:
        with neo4j_driver.session(database="neo4j") as session:
            results = session.run(
                CYPHER_FIND_LOW_ACCURACY_FOR_ALERT,
                accuracy_threshold=ACCURACY_THRESHOLD,
                time_range=historical_time_delta_iso
            )
            # Convert results and temporal types in metadata
            for record in results:
                 exp_data = record.data()
                 if 'metadata' in exp_data and exp_data['metadata']:
                     # Ensure metadata is JSON serializable
                     for key, value in exp_data['metadata'].items():
                          if hasattr(value, 'isoformat'):
                              exp_data['metadata'][key] = value.isoformat()
                          elif type(value).__name__ == 'Duration':
                              exp_data['metadata'][key] = str(value)

                 experiments_to_alert.append(exp_data)

    except ServiceUnavailable as e:
        logger.error(f"Neo4j connection error during alert check: {e}")
        return
    except Exception as e:
        logger.error(f"Neo4j query failed for alert check: {str(e)}")
        return

    num_found = len(experiments_to_alert)
    if num_found == 0:
        logger.info(f"No low-accuracy experiments found completed in the last {HISTORICAL_ALERT_CHECK_RANGE} days.")
        return

    logger.info(f"Found {num_found} potential low-accuracy experiments completed in the last {HISTORICAL_ALERT_CHECK_RANGE} days.")

    # Process Experiments (Check Redis, send alert, add to redis)
    alerts_sent_this_run = 0
    alert_uuid = "N/A"

    for exp in experiments_to_alert:  # Assuming experiments_to_alert is the list from Neo4j
        try:
            # get the required data from the experiment record
            exp_id = exp['experiment_id']
            accuracy_val = exp.get('accuracy')
            model_id = exp.get('model_id')
            metadata = exp.get('metadata')

            # Check Redis
            if redis_conn.sismember(REDIS_ALERTED_SET_KEY, exp_id):
                logger.debug(f"Experiment {exp_id} already alerted. Skipping.")
                continue

            # Create the alert Kafka event
            kafka_alert_message = create_low_accuracy_kafka_event(
                experiment_id=exp_id,
                accuracy=accuracy_val,
                model_id=model_id,
                metadata=metadata
            )
            alert_uuid = kafka_alert_message.get('UUID', 'N/A')

            # Send the alert
            future = kafka_producer.send(KAFKA_TOPIC, value=kafka_alert_message)
            future.add_errback(
                lambda exc: logger.error(f"Kafka send failed for experiment {exp_id} (UUID: {alert_uuid}): {exc}"))

            # Add the experiment id to redis
            redis_conn.sadd(REDIS_ALERTED_SET_KEY, exp_id)
            redis_conn.expire(REDIS_ALERTED_SET_KEY, REDIS_ALERTED_TTL_SECONDS)

            alerts_sent_this_run += 1
            accuracy_log = f"{accuracy_val:.2f}%" if isinstance(accuracy_val, (int, float)) else str(accuracy_val)
            logger.info(
                f"Alert sent for recently completed experiment {exp_id} with accuracy {accuracy_log} (UUID: {alert_uuid})")

        except KafkaError as e:
            log_uuid_k = alert_uuid if 'alert_uuid' in locals() and alert_uuid != "N/A" else 'N/A'
            logger.error(f"Kafka producer error for experiment {exp_id} (UUID: {log_uuid_k}): {str(e)}")
        except RedisError as e:
            log_uuid_r = alert_uuid if 'alert_uuid' in locals() and alert_uuid != "N/A" else 'N/A'
            logger.error(f"Redis operation failed for experiment {exp_id} (UUID: {log_uuid_r}): {str(e)}")
        except Exception as e:
            log_uuid_e = alert_uuid if 'alert_uuid' in locals() and alert_uuid != "N/A" else 'N/A'
            logger.error(f"Error processing alert for experiment {exp_id} (UUID: {log_uuid_e}): {str(e)}",
                         exc_info=True)

    logger.info(f"Alert check completed. Found {num_found} candidates completed in last {HISTORICAL_ALERT_CHECK_RANGE} days. Sent {alerts_sent_this_run} new alerts.")


def run_monitoring_tasks():
    """Runs the sequence of monitoring tasks."""
    logger.info("Starting monitoring cycle...")
    process_completed_experiments()
    check_low_accuracy_alerts()
    logger.info("Monitoring cycle completed.")


def shutdown():
    """Cleanup resources."""
    logger.info("Shutting down...")
    if kafka_producer:
        try:
            kafka_producer.flush()
            kafka_producer.close(timeout=10)
            logger.info("Kafka producer closed.")
        except Exception as e: logger.error(f"Error closing Kafka producer: {e}")
    if neo4j_driver:
        try:
            neo4j_driver.close()
            logger.info("Neo4j driver closed.")
        except Exception as e: logger.error(f"Error closing Neo4j driver: {e}")
    if redis_pool:
        try:
            redis_pool.disconnect()
            logger.info("Redis connection pool disconnected.")
        except Exception as e: logger.error(f"Error disconnecting Redis pool: {e}")
    logger.info("Cleanup completed.")


if __name__ == "__main__":
    scheduler = None
    try:
        redis_conn = get_redis_connection()
        neo4j_driver = initialize_neo4j_driver()
        kafka_producer = initialize_kafka_producer()

        if not all([redis_conn, neo4j_driver, kafka_producer]):
             raise RuntimeError("Failed to initialize one or more components. Exiting.")

        # Schedule the combined task function
        scheduler = BlockingScheduler(timezone="UTC")
        scheduler.add_job(run_monitoring_tasks, 'interval', minutes=SCHEDULE_IN_MIN, id='monitoring_tasks_job')

        logger.info(f'Experiment monitor starting. Running tasks every {SCHEDULE_IN_MIN} minute(s)...')
        scheduler.start()

    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown signal received.")
    except RuntimeError as e:
         logger.error(f"Runtime error during startup: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if scheduler and scheduler.running:
            scheduler.shutdown()
        shutdown()