import sys
import os

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.insert(0, BASE_DIR)

import dash
from dash import dcc, html, Input, Output, State, dash_table

from backend.db_auth import validate_user
from backend.order_service import save_order, get_orders

app = dash.Dash(__name__)
server = app.server


app.layout = html.Div([

    html.H2("Manual Production Order"),

    html.Hr(),

    html.H3("Employee Login"),

    dcc.Input(
        id="emp_id",
        type="text",
        placeholder="Employee ID"
    ),

    html.Br(),
    html.Br(),

    dcc.Input(
        id="password",
        type="password",
        placeholder="Password"
    ),

    html.Br(),
    html.Br(),

    html.Button(
        "Login",
        id="login_btn"
    ),

    html.Br(),
    html.Br(),

    html.Div(id="login_status"),

    dcc.Store(id="logged_user"),

    html.Div(
        id="main_ui",
        style={"display": "none"},
        children=[

            html.Hr(),

            html.H3("Production Order Entry"),

            html.Br(),

            dcc.Input(
                id="plant",
                type="text",
                placeholder="Plant"
            ),

            html.Br(),
            html.Br(),

            dcc.Input(
                id="part_no",
                type="text",
                placeholder="Part Number"
            ),

            html.Br(),
            html.Br(),

            dcc.Input(
                id="quantity",
                type="number",
                placeholder="Quantity"
            ),

            html.Br(),
            html.Br(),

            html.Button(
                "Submit Entry",
                id="submit_btn"
            ),

            html.Br(),
            html.Br(),

            html.Div(
                id="submit_status",
                style={
                    "fontWeight": "bold",
                    "color": "green"
                }
            ),

            html.Hr(),

            html.H3("Order History"),

            dash_table.DataTable(
                id="history_table",
                columns=[
                    {"name":"ID","id":"ID"},
                    {"name":"Employee","id":"Employee"},
                    {"name":"Plant","id":"Plant"},
                    {"name":"Part No","id":"Part No"},
                    {"name":"Quantity","id":"Quantity"},
                    {"name":"Unit Price","id":"Unit Price"},
                    {"name":"Value","id":"Value"},
                    {"name":"Status","id":"Status"},
                    {"name":"Approved By","id":"Approved By"},
                    {"name":"Approved At","id":"Approved At"}
                ],
                data=[],
                page_size=10,
                style_table={
                    "overflowX": "auto"
                },
                style_cell={
                    "textAlign": "left",
                    "padding": "8px"
                }
            )
        ]
    )
])


# LOGIN
@app.callback(
    Output("login_status", "children"),
    Output("main_ui", "style"),
    Output("logged_user", "data"),
    Output("history_table", "data"),
    Input("login_btn", "n_clicks"),
    State("emp_id", "value"),
    State("password", "value"),
    prevent_initial_call=True
)
def login(n_clicks, emp_id, password):

    if not emp_id or not password:
        return (
            "Enter Employee ID and Password",
            {"display": "none"},
            None,
            []
        )

    if validate_user(emp_id, password):

        orders = get_orders(emp_id)

        return (
            f"Welcome {emp_id}",
            {"display": "block"},
            emp_id,
            orders
        )

    return (
        "Invalid Login",
        {"display": "none"},
        None,
        []
    )


# SAVE ORDER
@app.callback(
    Output("submit_status", "children"),
    Output("history_table", "data", allow_duplicate=True),
    Input("submit_btn", "n_clicks"),
    State("plant", "value"),
    State("part_no", "value"),
    State("quantity", "value"),
    State("logged_user", "data"),
    prevent_initial_call=True
)
def submit_entry(
    n_clicks,
    plant,
    part_no,
    quantity,
    user_id
):

    if not user_id:
        return (
            "Please Login First",
            []
        )

    if not plant or not part_no or quantity is None:
        return (
            "Fill all fields",
            get_orders(user_id)
        )

    try:

        save_order(
            employee_id=user_id,
            plant=plant,
            part_no=part_no,
            quantity=quantity
        )

        orders = get_orders(user_id)

        return (
            "Order Saved Successfully",
            orders
        )

    except Exception as e:

        return (
            f"Error : {str(e)}",
            get_orders(user_id)
        )


if __name__ == "__main__":
    app.run(debug=True)