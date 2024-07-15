import json
import random
import threading
import panel as pn
from confluent_kafka import Consumer
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

pn.extension(sizing_mode="stretch_width")

CONFIG = {
    'bootstrap.servers': '129.114.35.150:9092',
    'group.id': f'ckn-analytics-dashboard-{random.randint(1, 1000)}',
    'auto.offset.reset': 'earliest'
}

# Create a separate consumer for each topic to avoid potential issues with sharing a single consumer instance
def create_consumer():
    return Consumer(CONFIG)

alert_stream = pn.pane.JSON()
event_stream = pn.pane.JSON()

# General function to consume messages from Kafka
def consume_topic(topic_name, update_function):
    consumer = create_consumer()
    consumer.subscribe([topic_name])

    while True:
        msg = consumer.poll(1.0)
        if msg is not None and not msg.error():
            event = json.loads(msg.value().decode('utf-8')) if msg.value() is not None else None
            if event:
                pn.state.execute(lambda: update_function(event))

def update_alert_stream(event):
    alert_stream.object = json.dumps(event, indent=2)

def update_event_stream(event):
    event_stream.object = json.dumps(event, indent=2)

# Start Kafka consumers in separate threads
threading.Thread(target=consume_topic, args=("oracle-alerts", update_alert_stream), daemon=True).start()
threading.Thread(target=consume_topic, args=("oracle-events", update_event_stream), daemon=True).start()

alerts_card = pn.Card(alert_stream, title="Alerts")
events_card = pn.Card(event_stream, title="Events")
checkbox = pn.widgets.Checkbox(name='Show saved events only')

source = ColumnDataSource(data={'time': [], 'probability': []})
plot = figure(title="Score Probability Over Time", x_axis_type='datetime', height=330, sizing_mode='stretch_width')
plot.line(x='time', y='probability', source=source, line_width=2)
plot.xaxis.axis_label = 'Time'
plot.yaxis.axis_label = 'Score Probability'

# Create the FastListTemplate
template = pn.template.FastListTemplate(
    title="CKN Analytics Dashboard",
    main=[alerts_card, events_card, plot],
    logo="https://www.iu.edu/images/brand/brand-expression/iu-trident-promo.jpg",
    accent="#990000"
)

# Serve the template
template.servable()
