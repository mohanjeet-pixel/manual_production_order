from dash import Input, Output, State, html

from backend.repositories.product_repository import get_part_price
from backend.services.batch_service import create_batch
from backend.services.order_service import get_orders
from backend.utils.exceptions import AppError

_ROWS = 5


def _ok(msg):
    return html.Div(msg, className="msg-ok")


def _err(msg):
    return html.Div(msg, className="msg-err")


def register(app):

    # ── live total across all rows ─────────────────────────────
    @app.callback(
        Output("batch-total", "children"),
        *[Input(f"batch-part-{i}", "value") for i in range(_ROWS)],
        *[Input(f"batch-qty-{i}",  "value") for i in range(_ROWS)],
    )
    def update_total(*args):
        parts = args[:_ROWS]
        qtys  = args[_ROWS:]
        total = 0.0
        for part, qty in zip(parts, qtys):
            if not part or not qty:
                continue
            price = get_part_price(part.strip())
            if price and qty:
                total += float(qty) * price
        return f"₹ {total:,.2f}" if total else "—"

    # ── submit batch ───────────────────────────────────────────
    @app.callback(
        Output("batch-msg",    "children"),
        Output("store-orders", "data",     allow_duplicate=True),
        Input("batch-submit",  "n_clicks"),
        *[State(f"batch-plant-{i}", "value") for i in range(_ROWS)],
        *[State(f"batch-part-{i}",  "value") for i in range(_ROWS)],
        *[State(f"batch-qty-{i}",   "value") for i in range(_ROWS)],
        State("store-user", "data"),
        prevent_initial_call=True,
    )
    def submit_batch(_, *args):
        plants  = args[0          : _ROWS]
        parts   = args[_ROWS      : _ROWS * 2]
        qtys    = args[_ROWS * 2  : _ROWS * 3]
        user_id = args[_ROWS * 3]

        if not user_id:
            return _err("Please log in first."), []

        items = []
        for plant, part, qty in zip(plants, parts, qtys):
            if plant and part and qty:
                items.append({
                    "plant":    plant.strip(),
                    "part_no":  part.strip(),
                    "quantity": float(qty),
                })

        if not items:
            return _err("Add at least one complete row (Plant, Part No, Quantity)."), \
                   get_orders(user_id)

        try:
            batch_id = create_batch(user_id, items)
            return (
                _ok(f"Batch {batch_id} created — {len(items)} order(s) submitted. Approval email sent."),
                get_orders(user_id),
            )
        except AppError as e:
            return _err(e.message), get_orders(user_id)
        except Exception as e:
            return _err(str(e)), get_orders(user_id)
