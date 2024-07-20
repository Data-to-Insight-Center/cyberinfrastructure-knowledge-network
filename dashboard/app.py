import os
import panel as pn
import pandas as pd
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

def load_alerts(nrows=10):
    return ckn_kg.fetch_alerts(nrows)

data = load_raw_data()
alerts = load_alerts()

accuracy = pn.indicators.Number(name='Accuracy', value=84, format='{value}%')
users = pn.indicators.Number(name='Users', value=3, format='{value}')
images = pn.indicators.Number(name='Images', value=45, format='{value}')
devices = pn.indicators.Number(name='Devices', value=12, format='{value}')

# Create a FlexBox layout to evenly distribute the space
indicators = pn.layout.FlexBox(
    pn.panel(accuracy, sizing_mode='stretch_width'),
    pn.panel(users, sizing_mode='stretch_width'),
    pn.panel(images, sizing_mode='stretch_width'),
    pn.panel(devices, sizing_mode='stretch_width'),
    align_items='stretch',
    justify_content='space-between'
)

alerts_table = pn.widgets.Tabulator(alerts, pagination="local", header_filters=True, layout='fit_data')

main = pn.Column(indicators, pn.Row(alerts_table))
template = pn.template.FastListTemplate(
    title="CKN Analytics Dashboard",
    main=[main],
    accent="#990000"
)

template.servable()