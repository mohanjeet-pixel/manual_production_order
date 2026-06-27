from dash import Input, Output, State, html

from backend.database.auth import validate_user
from backend.services.order_service import get_orders


def register(app):

    @app.callback(
        Output("login-msg",   "children"),
        Output("login-page",  "style"),
        Output("main-app",    "style"),
        Output("store-user",  "data"),
        Output("store-orders","data"),
        Output("header-user", "children"),
        Input("login-btn", "n_clicks"),
        State("login-emp-id", "value"),
        State("login-password", "value"),
        prevent_initial_call=True,
    )
    def login(_, emp_id, password):
        hidden = {"display": "none"}
        flex   = {"display": "flex"}
        block  = {"display": "block"}

        if not emp_id or not password:
            return (
                html.Div("Please enter Employee ID and Password.", className="login-msg-error"),
                flex, hidden, None, [], "",
            )

        if validate_user(emp_id.strip(), password):
            orders = get_orders(emp_id.strip())
            return (
                "",
                hidden, block,
                emp_id.strip(),
                orders,
                f"👤  {emp_id.strip()}",
            )

        return (
            html.Div("Invalid Employee ID or Password.", className="login-msg-error"),
            flex, hidden, None, [], "",
        )

    @app.callback(
        Output("login-page",   "style",  allow_duplicate=True),
        Output("main-app",     "style",  allow_duplicate=True),
        Output("store-user",   "data",   allow_duplicate=True),
        Output("store-orders", "data",   allow_duplicate=True),
        Output("header-user",  "children", allow_duplicate=True),
        Input("logout-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def logout(_):
        return {"display": "flex"}, {"display": "none"}, None, [], ""
