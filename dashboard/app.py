import asyncio
import json
import random
import threading
import numpy as np
import panel as pn
from confluent_kafka import Consumer
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
import os

pn.extension(sizing_mode="stretch_width")

CKN_KAFKA_BROKER = os.getenv('CKN_KAFKA_BROKER', 'localhost:9092')
DASHBOARD_GROUP_ID = os.getenv('DASHBOARD_GROUP_ID', 'ckn-analytics-dashboard')
CKN_KAFKA_OFFSET = os.getenv('CKN_KAFKA_OFFSET', 'earliest')
ORACLE_EVENTS_TOPIC = os.getenv('ORACLE_EVENTS_TOPIC', 'oracle-events')
ORACLE_ALERTS_TOPIC = os.getenv('ORACLE_ALERTS_TOPIC', 'oracle-alerts')

CONFIG = {
    'bootstrap.servers': CKN_KAFKA_BROKER,
    'group.id': DASHBOARD_GROUP_ID,
    'auto.offset.reset': CKN_KAFKA_OFFSET
}

def create_consumer():
    return Consumer(CONFIG)

alert_stream = pn.pane.JSON()
event_stream = pn.pane.JSON()
xs, ys = [], []

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
    xs.append(event["image_receiving_timestamp"])
    ys.append(event["probability"])

threading.Thread(target=consume_topic, args=(ORACLE_ALERTS_TOPIC, update_alert_stream), daemon=True).start()
threading.Thread(target=consume_topic, args=(ORACLE_EVENTS_TOPIC, update_event_stream), daemon=True).start()

alerts_card = pn.Card(alert_stream, title="Alerts")
events_card = pn.Card(event_stream, title="Events", collapsed=True)
checkbox = pn.widgets.Checkbox(name='Show saved events only')

p = figure(sizing_mode='stretch_width', title='Probability Over Time')
cds = ColumnDataSource(data={'x': xs, 'y': ys})
p.line('x', 'y', source=cds)

def stream():
    if xs and ys:
        cds.stream({'x': [xs[-1]], 'y': [ys[-1]]})

cb = pn.state.add_periodic_callback(stream, 100)

bk_pane = pn.pane.Bokeh(p)

template = pn.template.FastListTemplate(
    title="CKN Analytics Dashboard",
    main=[alerts_card, events_card, bk_pane],
    logo="https://www.iu.edu/images/brand/brand-expression/iu-trident-promo.jpg",
    accent="#990000"
)

template.servable()
