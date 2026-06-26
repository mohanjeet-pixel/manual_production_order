from dash import Input, Output, State

from backend.database.auth import validate_user
from backend.services.order_service import get_orders


def register(app):

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
