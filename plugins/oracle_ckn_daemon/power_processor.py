import json
import os
import time
import logging


class PowerProcessor:
    """
    Processes the power events and sends events to the CKN Broker.
    """

    def __init__(self,
                 power_summary_file,
                 kafka_producer,
                 topic,
                 experiment_id,
                 max_attempts=5,
                 timeout=10):
        self.power_summary_file = power_summary_file
        self.kafka_producer = kafka_producer
        self.topic = topic
        self.experiment_id = experiment_id
        self.max_attempts = max_attempts
        self.timeout = timeout

    def get_power_summary(self):
        """
        Reads the power summary from the power summary file.
        :return:
        """
        with open(self.power_summary_file, 'r') as file:
            data = json.load(file)

        # Extract the plugin power summary report
        power_summary = data["plugin power summary report"]

        # Initialize a dictionary for the flattened event
        flattened_event = {}

        # Initialize total CPU and GPU consumption
        total_cpu_consumption = 0.0
        total_gpu_consumption = 0.0

        # Iterate over each plugin's data and add it to the flattened event
        for plugin_data in power_summary:
            plugin_name = plugin_data["plugin"]

            # Add plugin's CPU and GPU consumption to the flattened event
            cpu_consumption = plugin_data["cpu_power_consumption"]
            gpu_consumption = plugin_data["gpu_power_consumption"]

            flattened_event[
                f"{plugin_name}_cpu_power_consumption"] = cpu_consumption
            flattened_event[
                f"{plugin_name}_gpu_power_consumption"] = gpu_consumption

            # Accumulate total CPU and GPU consumption
            total_cpu_consumption += cpu_consumption
            total_gpu_consumption += gpu_consumption

        # Add total CPU and GPU consumption and experiment ID to the flattened event
        flattened_event["total_cpu_power_consumption"] = total_cpu_consumption
        flattened_event["total_gpu_power_consumption"] = total_gpu_consumption
        flattened_event["experiment_id"] = self.experiment_id

        return flattened_event

    def process_summary_events(self):
        """
        Waits for the summary to be available and processes it.
        :return:
        """
        attempt = 0
        # read the file if it's available. total wait time
        while attempt < self.max_attempts:
            if os.path.exists(self.power_summary_file):
                logging.info("Reading the power summary file...")

                # read the power summary
                power_summary = self.get_power_summary()
                power_summary_json = json.dumps(power_summary)

                # send the event to kafka
                self.kafka_producer.produce(self.topic,
                                            key=self.experiment_id,
                                            value=power_summary_json)
                self.kafka_producer.flush()
                return
            # Increment the attempt count and wait before trying again
            attempt += 1
            time.sleep(self.timeout)

        logging.info("No power summary file found...")
