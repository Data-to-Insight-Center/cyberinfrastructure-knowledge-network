import json
import threading
import panel as pn
from confluent_kafka import Consumer
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

pn.extension(sizing_mode="stretch_width")

streaming_component = pn.pane.JSON()
checkbox = pn.widgets.Checkbox(name='Show saved events only')

source = ColumnDataSource(data={'time': [], 'probability': []})
plot = figure(title="Score Probability Over Time", x_axis_type='datetime', height=330, sizing_mode='stretch_width')
plot.line(x='time', y='probability', source=source, line_width=2)
plot.xaxis.axis_label = 'Time'
plot.yaxis.axis_label = 'Score Probability'

# Function to consume messages from Kafka
def consume_messages():
    config = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'ckn-analytics-dashboard',
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(config)
    consumer.subscribe(["oracle-alerts"])

    while True:
        msg = consumer.poll(1.0)
        if msg is not None and not msg.error():
            event = json.loads(msg.value().decode('utf-8')) if msg.value() is not None else None
            if event:
                print(event)
                # Update the streaming component with the event in a thread-safe manner
                pn.state.execute(lambda: update_streaming_component(event))

def update_streaming_component(event):
    streaming_component.object = json.dumps(event, indent=2)

# Start Kafka consumer in a separate thread
threading.Thread(target=consume_messages, daemon=True).start()

# Create the FastListTemplate
template = pn.template.FastListTemplate(
    title="CKN Analytics Dashboard",
    sidebar=[pn.Column(checkbox)],
    main=[pn.Card(streaming_component, title="Alerts", collapsible=False),
          plot],
    logo="https://www.iu.edu/images/brand/brand-expression/iu-trident-promo.jpg",
    accent="#990000"
)

# Serve the template
template.servable()
