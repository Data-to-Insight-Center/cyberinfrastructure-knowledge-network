import os
import panel as pn
import pandas as pd
import datetime as dt
from bokeh.plotting import figure

from dotenv import load_dotenv
from ckn_kg import CKNKnowledgeGraph

pn.extension("tabulator", sizing_mode="stretch_width")

load_dotenv()
CKN_KG_URI = os.getenv('NEO4J_URI')
CKN_KG_USER = os.getenv('NEO4J_USER')
CKN_KG_PWD = os.getenv('NEO4J_PWD')

ckn_kg = CKNKnowledgeGraph(CKN_KG_URI, CKN_KG_USER, CKN_KG_PWD)

# Fetch all options initially
experiment_options = ckn_kg.fetch_distinct_experiment_id()
device_options = ckn_kg.fetch_distinct_devices()
user_options = ckn_kg.fetch_distinct_users()

# Initialize widgets with all options selected
experiment_widget = pn.widgets.MultiChoice(value=[], placeholder="Experiment", options=experiment_options)
device_widget = pn.widgets.MultiChoice(value=[], placeholder="Device", options=device_options)
user_widget = pn.widgets.MultiChoice(value=[], placeholder="User", options=user_options)
date_range_picker = pn.widgets.DatetimeRangePicker(value=(dt.date(2024, 7, 18), dt.date(2024, 7, 19)))
decision_widget = pn.widgets.RadioButtonGroup(value='Saved', options=['Saved', 'Deleted'], height=40)

def update(event=None):
    stats = ckn_kg.get_statistics(
        experiment_ids=experiment_widget.value,
        device_ids=device_widget.value,
        user_ids=user_widget.value,
        date_range=date_range_picker.value,
        image_decision=decision_widget.value
    )
    average_probability = stats.get('average_probability', 0) or 0
    indicators = {
        'Accuracy': pn.indicators.Number(name='Accuracy', value=round(average_probability * 100), format='{value}%', font_size='24pt'),
        'Users': pn.indicators.Number(name='Users', value=stats.get('user_count', 0), format='{value}', font_size='24pt'),
        'Images': pn.indicators.Number(name='Images', value=stats.get('image_count', 0), format='{value}', font_size='24pt'),
        'Devices': pn.indicators.Number(name='Devices', value=stats.get('device_count', 0), format='{value}', font_size='24pt')
    }

    indicators_panel[:] = [
        pn.panel(indicator, sizing_mode='stretch_width') for indicator in indicators.values()
    ]

    # Update the accuracy trend plot
    accuracy_trend_df = ckn_kg.fetch_accuracy_trend(date_range_picker.value, decision_widget.value == 'Saved')
    accuracy_trend_df['image_scoring_timestamp'] = pd.to_datetime(accuracy_trend_df['image_scoring_timestamp'])
    
    p.renderers = []  # Clear existing renderers
    p.line(accuracy_trend_df['image_scoring_timestamp'], accuracy_trend_df['probability'], line_width=2)

    # Update the alerts table
    alerts_table.value = ckn_kg.fetch_alerts()

stats = ckn_kg.get_statistics()
indicators_panel = pn.layout.FlexBox(
    pn.panel(pn.indicators.Number(name='Accuracy', value=stats["average_probability"], format='{value}%', font_size='24pt'), sizing_mode='stretch_width'),
    pn.panel(pn.indicators.Number(name='Users', value=stats["user_count"], format='{value}', font_size='24pt'), sizing_mode='stretch_width'),
    pn.panel(pn.indicators.Number(name='Images', value=stats["image_count"], format='{value}', font_size='24pt'), sizing_mode='stretch_width'),
    pn.panel(pn.indicators.Number(name='Devices', value=stats["device_count"], format='{value}', font_size='24pt'), sizing_mode='stretch_width'),
    align_items='stretch', justify_content='space-between'
)

experiment_widget.param.watch(update, 'value')
device_widget.param.watch(update, 'value')
user_widget.param.watch(update, 'value')
date_range_picker.param.watch(update, 'value')
decision_widget.param.watch(update, 'value')

# Initial plot setup without any filters
accuracy_trend_df = ckn_kg.fetch_accuracy_trend(date_range_picker.value, decision_widget.value == 'Saved')
accuracy_trend_df['image_scoring_timestamp'] = pd.to_datetime(accuracy_trend_df['image_scoring_timestamp'])
p = figure(title='Accuracy Trend', x_axis_type='datetime', height=400, sizing_mode="stretch_width")
p.line(accuracy_trend_df['image_scoring_timestamp'], accuracy_trend_df['probability'], line_width=2)

alerts_table = pn.widgets.Tabulator(ckn_kg.fetch_alerts(), pagination="local", header_filters=True, layout='fit_data', page_size=10)

widgets_panel = pn.layout.FlexBox(
    pn.Row(experiment_widget, device_widget, user_widget, date_range_picker, decision_widget),
    align_items='stretch', justify_content='space-between'
)

main = pn.Column(widgets_panel, indicators_panel, p, pn.Card(alerts_table, title="Alerts"))

template = pn.template.FastListTemplate(title="CKN Analytics Dashboard", main=[main], accent="#990000", theme="dark")

template.servable()
