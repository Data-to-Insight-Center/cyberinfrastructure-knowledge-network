import threading
from kafka import KafkaConsumer
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
import panel as pn
import json
from datetime import datetime

# Set up Panel
pn.extension()

# Global variable to store messages
messages = []

# Create a Panel TextAreaInput widget to display the log
log_pane = pn.widgets.TextAreaInput(value='', height=340, width=800, disabled=True, sizing_mode='stretch_width')

# ColumnDataSource for the Bokeh plot
source = ColumnDataSource(data={'time': [], 'probability': []})
plot = figure(title="Score Probability Over Time", x_axis_type='datetime', height=340, width=800, sizing_mode='stretch_width')
plot.line(x='time', y='probability', source=source, line_width=2)
plot.xaxis.axis_label = 'Time'
plot.yaxis.axis_label = 'Score Probability'

# Function to consume Kafka messages
def consume_messages():
    consumer = KafkaConsumer('accuracy', bootstrap_servers=['localhost:56310'])
    for message in consumer:
        message_value = json.loads(message.value.decode('utf-8'))
        messages.append(message_value)
        update_log(message_value)
        update_plot(message_value)
# Function to update the log in the Panel dashboard
def update_log(new_message):
    log_pane.value += json.dumps(new_message, indent=2) + '\n\n'
    log_pane.param.trigger('value')  # Manually trigger the update to the value property

# Function to update the Bokeh plot
def update_plot(new_message):
    new_data = {
        'time': [datetime.strptime(new_message["image_scoring_timestamp"], '%Y-%m-%dT%H:%M:%S.%f')],
        'probability': [new_message["score_probability"]]
    }
    source.stream(new_data, rollover=200)

# Start Kafka consumer in a separate thread
threading.Thread(target=consume_messages, daemon=True).start()

# Create a filter checkbox
filter_checkbox = pn.widgets.Checkbox(name='Show only "Save" decisions', value=True)

# Function to handle checkbox change
def on_checkbox_change(event):
    log_pane.value = ""
    source.data = {'time': [], 'probability': []}  # Clear the plot
    for message in messages:
        update_log(message)
        update_plot(message)

filter_checkbox.param.watch(on_checkbox_change, 'value')

# Create the FastListTemplate
template = pn.template.FastListTemplate(
    title="Cyberinfrastructure Knowledge Network",
    sidebar=[],
    main=[
        pn.Column(filter_checkbox,
                  log_pane, sizing_mode='stretch_width'),
        plot,
    ],
    accent_base_color="#DC143C",
    header_background="#DC143C",
)

# Serve the template
template.servable()
