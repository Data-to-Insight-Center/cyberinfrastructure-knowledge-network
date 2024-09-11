from confluent_kafka import Producer
import json
import os
from dotenv import load_dotenv

load_dotenv()
KAFKA_BROKER = os.getenv("KAFKA_BROKER")

# Define the Kafka producer configuration
kafka_conf = {'bootstrap.servers': KAFKA_BROKER, 'log_level': 0}

# Create a Kafka producer instance
producer = Producer(**kafka_conf)

# Define the event data as a dictionary
event_data = {
    "uuid": "3455s-4e0e-4abb-af35-dc89eb962ec1",
    "application_name": "cg.c",
    "program_location":
    "/mnt/d/workspace/ud-masters/benchmarks/NPB3.3-SER-C/CG/cg.c",
    "loop_id": "main#3",
    "DataSize": "((1+(-1*firstcol))+lastcol)",
    "Number_of_Iterations": "null",
    "total_of_Iterations": "null",
    "Number_of_Loads": "4",
    "Number_of_Stores": "null",
    "Number_of_Instructions": "4",
    "Number_of_Statements": "1",
    "Loopness_Level": "null",
    "No_of_Bits_per_iteration": "null",
    "No_of_Times_a_Data_Type_Changed": "null",
    "No_of_Integer_Operation_Type": "null",
    "No_of_Float_Operation_Type": "null",
    "No_of_Double_Operation_Type": "nan",
    "No_of_Long_Double_Operation": "null",
    "No_of_Long_Operation": "null",
    "No_of_Short_Operation": "null",
    "Big_O_Notation": "null",
    "No_of_multiplication": "null",
    "No_of_substraction": "True",
    "No_of_addition": "null",
    "No_of_Function_Calls_Side_effect_Free": "null",
    "Data_dependence_Free": "nan",
    "Ratio_of_Reduction_Statements": "nan",
    "Ratio_of_Flow_Dependences_Remaining": "nan"
}

# Convert the event data to a JSON string
event_json = json.dumps(event_data)

# Define the topic name
topic_name = 'compiler-data'


# Define a delivery report callback function
def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print(f'Delivery failed for message {msg.key()}: {err}')
    else:
        print(
            f'Message produced to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}'
        )


# Produce the message to the Kafka topic
producer.produce(topic_name, value=event_json, callback=delivery_report)

# Wait up to 1 second for events. Callbacks will be invoked during
# poll() if the message is successfully delivered or if delivery failed.
producer.poll(1)

# Flush all messages in the producer's queue
producer.flush()

print(f"Event data sent to topic '{topic_name}' successfully.")
