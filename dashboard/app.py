import os
import json

import panel as pn
import pandas as pd
import datetime as dt
from bokeh.plotting import figure
from dotenv import load_dotenv
from ckn_kg import CKNKnowledgeGraph
from panel.viewable import Viewable, Viewer

pn.extension("tabulator", sizing_mode="stretch_width")

load_dotenv()
CKN_KG_URI = os.getenv('NEO4J_URI')
CKN_KG_USER = os.getenv('NEO4J_USER')
CKN_KG_PWD = os.getenv('NEO4J_PWD')

class CKNAnalytics(Viewer):
    """Renders CKN Analytics Dashboard"""

    def __init__(self):
        super().__init__()

        self.ckn_kg = CKNKnowledgeGraph(CKN_KG_URI, CKN_KG_USER, CKN_KG_PWD)

        # Fetch widget options
        self.device_options = self.ckn_kg.fetch_distinct_devices()
        self.user_options = self.ckn_kg.fetch_distinct_users()
        self.experiment_options = self.ckn_kg.fetch_distinct_experiment_id()

        self.exp_info = self.ckn_kg.get_exp_info()
        self.exp_info_table = pn.widgets.Tabulator(self.exp_info, pagination="local", page_size=5,
                                                   header_filters={"Experiment": True, "User": True, "Model": True, "Device": True})
        
        self.alerts_info = self.ckn_kg.fetch_alerts()
        self.alerts_info_table = pn.Card(pn.widgets.Tabulator(self.alerts_info, pagination="local", page_size=5, header_filters=True), title="Alerts")

        experiment_options = self.ckn_kg.fetch_distinct_experiment_id()
        self.exp_widget = pn.widgets.Select(value=experiment_options[0], options=experiment_options)
        self.date_widget = pn.widgets.DatetimeRangePicker(value=(dt.date(2024, 7, 18), dt.date(2024, 7, 19)))
        self.button = pn.widgets.Button(name="Query")
        self.button.on_click(self.update_plot_data)

        self.raw_data = self.ckn_kg.get_exp_info_raw(self.exp_widget.value)
        self.raw_data_table = pn.widgets.Tabulator(self.raw_data, pagination="local", page_size=8)

        self.accuracy_trend_df = self.ckn_kg.fetch_accuracy_trend(self.date_widget.value, self.exp_widget.value)
        self.accuracy_trend_df['image_scoring_timestamp'] = pd.to_datetime(self.accuracy_trend_df['image_scoring_timestamp'])

        self.p = figure(title='Accuracy Trend', x_axis_type='datetime', height=300, sizing_mode="stretch_width")
        self.line_renderer = self.p.line(self.accuracy_trend_df['image_scoring_timestamp'], self.accuracy_trend_df['probability'], line_width=2)
        
        self.plot_data = pn.Column(pn.Row(self.exp_widget, self.date_widget, self.button), pn.Row(self.p, self.raw_data_table))

        self.template = pn.template.FastListTemplate(
            title="CKN Analytics Dashboard",
            main=[self.plot_data, self.exp_info_table, self.alerts_info_table],
            accent="#990000"
        )
        
    def update_plot_data(self, *_):
        accuracy_trend_df = self.ckn_kg.fetch_accuracy_trend(self.date_widget.value, self.exp_widget.value)
        accuracy_trend_df['image_scoring_timestamp'] = pd.to_datetime(accuracy_trend_df['image_scoring_timestamp'])
        
        # Update the Bokeh figure
        self.line_renderer.data_source.data = {
            'x': accuracy_trend_df['image_scoring_timestamp'],
            'y': accuracy_trend_df['probability']
        }

        # Update the Tabulator table
        self.raw_data = self.ckn_kg.get_exp_info_raw(self.exp_widget.value)
        self.raw_data_table.value = self.raw_data
    
    def __panel__(self) -> Viewable:
        return self.template
    
ckn = CKNAnalytics()
ckn.template.servable()
