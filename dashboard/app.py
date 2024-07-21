import os
import panel as pn
import pandas as pd
import datetime as dt
import panel as pn
from bokeh.plotting import figure

from dotenv import load_dotenv
from ckn_kg import CKNKnowledgeGraph

pn.extension("tabulator", sizing_mode="stretch_width")

load_dotenv()
CKN_KG_URI = os.getenv('NEO4J_URI')
CKN_KG_USER = os.getenv('NEO4J_USER')
CKN_KG_PWD = os.getenv('NEO4J_PWD')

ckn_kg = CKNKnowledgeGraph(CKN_KG_URI, CKN_KG_USER, CKN_KG_PWD)


def load_raw_data(nrows=50):
    latest_edges = ckn_kg.fetch_latest_served_by_edges(nrows)
    df = pd.DataFrame(latest_edges)
    return df


experiment_widget = pn.widgets.MultiChoice(
    name='Experiment ID', options=ckn_kg.fetch_distinct_experiment_id())
device_widget = pn.widgets.MultiChoice(name='Edge Device',
                                       options=ckn_kg.fetch_distinct_devices())
user_widget = pn.widgets.MultiChoice(name='User',
                                     options=ckn_kg.fetch_distinct_users())
date_range_picker = pn.widgets.DatetimeRangePicker(name='Date Range',
                                                   value=(dt.date(2024, 7, 18),
                                                          dt.date(2024, 7,
                                                                  19)))
decision_widget = pn.widgets.RadioButtonGroup(name='Image Decision',
                                              options=['Saved', 'Deleted'],
                                              align="center",
                                              height=40)

widgets_panel = pn.layout.FlexBox(pn.Row(experiment_widget, device_widget,
                                         user_widget, date_range_picker,
                                         decision_widget),
                                  align_items='stretch',
                                  justify_content='space-between')

stats = ckn_kg.get_statistics()
indicators = {
    'Accuracy':
    pn.indicators.Number(name='Accuracy',
                         value=round(stats['average_probability'] * 100),
                         format='{value}%',
                         font_size='24pt'),
    'Users':
    pn.indicators.Number(name='Users',
                         value=stats['user_count'],
                         format='{value}',
                         font_size='24pt'),
    'Images':
    pn.indicators.Number(name='Images',
                         value=stats['image_count'],
                         format='{value}',
                         font_size='24pt'),
    'Devices':
    pn.indicators.Number(name='Devices',
                         value=stats['device_count'],
                         format='{value}',
                         font_size='24pt')
}

indicators_panel = pn.layout.FlexBox(*[
    pn.panel(indicator, sizing_mode='stretch_width')
    for indicator in indicators.values()
],
                                     align_items='stretch',
                                     justify_content='space-between')

accuracy_trend_df = ckn_kg.fetch_accuracy_trend(date_range_picker.value)
accuracy_trend_df['image_scoring_timestamp'] = pd.to_datetime(
    accuracy_trend_df['image_scoring_timestamp'])
p = figure(title='Accuracy Trend',
           x_axis_type='datetime',
           height=400,
           sizing_mode="stretch_width")
p.line(accuracy_trend_df['image_scoring_timestamp'],
       accuracy_trend_df['probability'],
       line_width=2)

alerts_table = pn.widgets.Tabulator(ckn_kg.fetch_alerts(),
                                    pagination="local",
                                    header_filters=True,
                                    layout='fit_data',
                                    page_size=10)

main = pn.Column(widgets_panel, indicators_panel, p,
                 pn.Card(alerts_table, title="Alerts"))
template = pn.template.FastListTemplate(title="CKN Analytics Dashboard",
                                        main=[main],
                                        accent="#990000")

template.servable()
