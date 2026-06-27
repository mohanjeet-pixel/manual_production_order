from dash import Input, Output


def register(app):

    # ── dashboard stats ────────────────────────────────────────
    @app.callback(
        Output("stat-total",    "children"),
        Output("stat-pending",  "children"),
        Output("stat-approved", "children"),
        Output("stat-rejected", "children"),
        Output("stat-value",    "children"),
        Output("recent-table",  "data"),
        Input("store-orders", "data"),
    )
    def update_dashboard(orders):
        if not orders:
            return "0", "0", "0", "0", "₹ 0.00", []

        total     = len(orders)
        pending   = sum(1 for o in orders if o.get("Status") == "PENDING")
        approved  = sum(1 for o in orders if o.get("Status") == "APPROVED")
        rejected  = sum(1 for o in orders if o.get("Status") == "REJECTED")
        total_val = sum(float(o.get("Value") or 0) for o in orders)

        return (
            str(total),
            str(pending),
            str(approved),
            str(rejected),
            f"₹ {total_val:,.2f}",
            orders[:5],
        )

    # ── history table ──────────────────────────────────────────
    @app.callback(
        Output("history-table", "data"),
        Output("history-count", "children"),
        Input("store-orders",   "data"),
    )
    def update_history(orders):
        orders = orders or []
        label  = f"{len(orders)} order{'s' if len(orders) != 1 else ''}"
        return orders, label
