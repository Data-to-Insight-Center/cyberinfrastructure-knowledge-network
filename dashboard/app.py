#!/usr/bin/env python
import json
from datetime import datetime
import threading
import panel as pn
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from confluent_kafka import Consumer, KafkaError

pn.extension()

messages = []

log_pane = pn.widgets.TextAreaInput(value='', height=340, sizing_mode='stretch_width', disabled=True)

# ColumnDataSource for the Bokeh plot
source = ColumnDataSource(data={'time': [], 'probability': []})
plot = figure(title="Score Probability Over Time", x_axis_type='datetime', height=340, sizing_mode='stretch_width')
plot.line(x='time', y='probability', source=source, line_width=2)
plot.xaxis.axis_label = 'Time'
plot.yaxis.axis_label = 'Score Probability'

def consume_messages():
    config = {
        'bootstrap.servers': 'localhost:57581',
        'group.id': 'kafka-python-getting-started',
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(config)
    consumer.subscribe(["accuracy"])

    try:
        print("Starting Kafka consumer...")
        while True:
            msg = consumer.poll(1.0)
            if msg is not None:
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        print(f"Reached end of partition: {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
                    elif msg.error():
                        print(f"Consumer error: {msg.error()}")
                        continue

                event = json.loads(msg.value().decode('utf-8')) if msg.value() is not None else None
                print(f"Consumed message: {event}")
                if event:
                    messages.append(event)
                    update_log_and_plot(event)

            else:
                continue

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

def update_log(new_message):
    log_pane.value += json.dumps(new_message) + '\n\n'
    log_pane.param.trigger('value')  # Manually trigger the update to the value property

# Function to update the Bokeh plot
def update_plot(new_message):
    try:
        new_data = {
            'time': [datetime.strptime(new_message["image_scoring_timestamp"], '%Y-%m-%dT%H:%M:%S.%f')],
            'probability': [new_message["probability"]]
        }
        pn.state.execute(lambda: source.stream(new_data, rollover=200))
    except Exception as e:
        print(f"Error updating plot: {e}")

def update_log_and_plot(new_message):
    update_log(new_message)
    update_plot(new_message)

# Start Kafka consumer in a separate thread
threading.Thread(target=consume_messages, daemon=True).start()

# Create the FastListTemplate
template = pn.template.FastListTemplate(
    title="Cyberinfrastructure Knowledge Network",
    sidebar=[],
    main=[
        pn.Column(log_pane, sizing_mode='stretch_width'),
        plot,
    ],
    theme="dark",
    accent_base_color="#DC143C",
    header_background="#DC143C",
)

# Serve the template
template.servable()
