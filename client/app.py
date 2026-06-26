import sys
import os

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.insert(0, BASE_DIR)

import dash

from client.layout.main import layout
from client.callbacks import register

app = dash.Dash(__name__)
server = app.server

app.layout = layout

register(app)

if __name__ == "__main__":
    app.run(debug=True)
