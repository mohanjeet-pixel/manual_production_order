from dash import Input, Output, State, html

from backend.repositories.product_repository import get_part_price
from backend.services.order_service import save_order, get_orders
from backend.utils.exceptions import AppError


def _ok(msg):
    return html.Div(msg, className="msg-ok")


def _err(msg):
    return html.Div(msg, className="msg-err")


def register(app):

    # ── live price + value lookup ──────────────────────────────
    @app.callback(
        Output("order-price", "children"),
        Output("order-value", "children"),
        Input("order-part",  "value"),
        Input("order-qty",   "value"),
        State("store-user",  "data"),
        prevent_initial_call=True,
    )
    def lookup_price(part_no, qty, user_id):
        if not user_id or not part_no:
            return "—", "—"

        price = get_part_price(part_no.strip())
        if price is None:
            return "Part not found", "—"

        qty_val = float(qty) if qty else 0.0
        value   = qty_val * price
        return f"₹ {price:,.2f}", f"₹ {value:,.2f}"

    # ── submit order ───────────────────────────────────────────
    @app.callback(
        Output("order-msg",    "children"),
        Output("store-orders", "data",     allow_duplicate=True),
        Output("order-plant",  "value"),
        Output("order-part",   "value"),
        Output("order-qty",    "value"),
        Input("order-submit",  "n_clicks"),
        State("order-plant",   "value"),
        State("order-part",    "value"),
        State("order-qty",     "value"),
        State("store-user",    "data"),
        prevent_initial_call=True,
    )
    def submit_order(_, plant, part_no, qty, user_id):
        if not user_id:
            return _err("Please log in first."), [], plant, part_no, qty

        if not plant or not part_no or qty is None:
            return _err("Fill all fields: Plant, Part Number and Quantity."), \
                   get_orders(user_id), plant, part_no, qty

        try:
            save_order(
                employee_id=user_id,
                plant=plant.strip(),
                part_no=part_no.strip(),
                quantity=float(qty),
            )
            return (
                _ok("Order submitted — approval email sent to approver."),
                get_orders(user_id),
                None, None, None,          # clear form
            )
        except AppError as e:
            return _err(e.message), get_orders(user_id), plant, part_no, qty
        except Exception as e:
            return _err(str(e)), get_orders(user_id), plant, part_no, qty

    # ── clear form ─────────────────────────────────────────────
    @app.callback(
        Output("order-plant", "value",    allow_duplicate=True),
        Output("order-part",  "value",    allow_duplicate=True),
        Output("order-qty",   "value",    allow_duplicate=True),
        Output("order-price", "children", allow_duplicate=True),
        Output("order-value", "children", allow_duplicate=True),
        Output("order-msg",   "children", allow_duplicate=True),
        Input("order-clear",  "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_form(_):
        return None, None, None, "—", "—", ""
