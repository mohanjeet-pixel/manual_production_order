from dash import Input, Output, State

from backend.services.order_service import save_order, get_orders


def register(app):

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
    def submit_entry(n_clicks, plant, part_no, quantity, user_id):

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

            return (
                "Order Saved Successfully",
                get_orders(user_id)
            )

        except Exception as e:

            return (
                f"Error : {str(e)}",
                get_orders(user_id)
            )
