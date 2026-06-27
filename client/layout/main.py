from dash import dcc, html, dash_table

# ── helpers ───────────────────────────────────────────────────


def _label(text):
    return html.Div(text, className="field-label")


def _field_input(id_, placeholder, type_="text", debounce=False):
    return dcc.Input(
        id=id_,
        type=type_,
        placeholder=placeholder,
        className="field-input",
        debounce=debounce,
        style={"width": "100%"},
    )


def _display(id_, default="—"):
    return html.Div(default, id=id_, className="field-display")


# ── LOGIN PAGE ─────────────────────────────────────────────────

login_page = html.Div(
    id="login-page",
    className="login-page",
    style={"display": "flex"},
    children=[
        html.Div(className="login-card", children=[

            html.Div(className="login-brand", children=[
                html.Span("🏭", className="login-icon"),
                html.Div("Bull Machines", className="login-brand-title"),
                html.Div("Manual Production Orders", className="login-brand-sub"),
            ]),

            html.Div(className="form-group", children=[
                html.Label("Employee ID", className="form-label"),
                dcc.Input(
                    id="login-emp-id",
                    type="text",
                    placeholder="Enter Employee ID",
                    className="form-input",
                    debounce=False,
                    n_submit=0,
                    style={"width": "100%"},
                ),
            ]),

            html.Div(className="form-group", children=[
                html.Label("Password", className="form-label"),
                dcc.Input(
                    id="login-password",
                    type="password",
                    placeholder="Enter Password",
                    className="form-input",
                    debounce=False,
                    n_submit=0,
                    style={"width": "100%"},
                ),
            ]),

            html.Button("Login  →", id="login-btn", className="btn-primary"),
            html.Div(id="login-msg"),
        ]),
    ],
)


# ── DASHBOARD TAB ──────────────────────────────────────────────

dashboard_tab = html.Div(className="page-body", children=[

    html.Div(className="page-title", children=["📊  Dashboard"]),

    # Stat cards
    html.Div(className="stats-row", children=[
        html.Div(className="stat-card", children=[
            html.Div("Total Orders", className="stat-label"),
            html.Div("—", id="stat-total", className="stat-number"),
            html.Div("all time", className="stat-hint"),
        ]),
        html.Div(className="stat-card pending", children=[
            html.Div("Pending", className="stat-label"),
            html.Div("—", id="stat-pending", className="stat-number"),
            html.Div("awaiting approval", className="stat-hint"),
        ]),
        html.Div(className="stat-card approved", children=[
            html.Div("Approved", className="stat-label"),
            html.Div("—", id="stat-approved", className="stat-number"),
            html.Div("orders approved", className="stat-hint"),
        ]),
        html.Div(className="stat-card rejected", children=[
            html.Div("Rejected", className="stat-label"),
            html.Div("—", id="stat-rejected", className="stat-number"),
            html.Div("orders rejected", className="stat-hint"),
        ]),
    ]),

    # Total value banner
    html.Div(className="value-banner", children=[
        html.Div([
            html.Div("Total Order Value", className="value-banner-label"),
            html.Div("—", id="stat-value", className="value-banner-amount"),
        ]),
        html.Div("📈", style={"fontSize": "36px", "opacity": "0.5"}),
    ]),

    # Recent orders
    html.Div(className="card", children=[
        html.Div(className="card-header", children=[
            html.Span("🕐  Recent Orders"),
            html.Span("Last 5 orders", style={"fontSize": "12px", "fontWeight": "400", "color": "#64748b"}),
        ]),
        html.Div(className="card-body", children=[
            dash_table.DataTable(
                id="recent-table",
                columns=[
                    {"name": "ID",       "id": "ID"},
                    {"name": "Plant",    "id": "Plant"},
                    {"name": "Part No",  "id": "Part No"},
                    {"name": "Quantity", "id": "Quantity"},
                    {"name": "Value",    "id": "Value"},
                    {"name": "Status",   "id": "Status"},
                    {"name": "Date",     "id": "created_at"},
                ],
                data=[],
                page_size=5,
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "fontFamily": "Inter, sans-serif", "fontSize": "13px", "padding": "10px 14px"},
                style_header={"background": "#f8fafc", "fontWeight": "600", "fontSize": "11px",
                               "textTransform": "uppercase", "letterSpacing": "0.4px", "color": "#64748b",
                               "borderBottom": "2px solid #e0e4ea"},
                style_data={"borderBottom": "1px solid #f0f2f5"},
                style_data_conditional=[
                    {"if": {"filter_query": '{Status} = "PENDING"',  "column_id": "Status"},
                     "color": "#ed6c02", "fontWeight": "700"},
                    {"if": {"filter_query": '{Status} = "APPROVED"', "column_id": "Status"},
                     "color": "#2e7d32", "fontWeight": "700"},
                    {"if": {"filter_query": '{Status} = "REJECTED"', "column_id": "Status"},
                     "color": "#c62828", "fontWeight": "700"},
                ],
                style_as_list_view=True,
            ),
        ]),
    ]),
])


# ── NEW ORDER TAB ──────────────────────────────────────────────

new_order_tab = html.Div(className="page-body", children=[

    html.Div(className="page-title", children=["➕  New Production Order"]),

    html.Div(className="card", children=[
        html.Div("Order Details", className="card-header"),
        html.Div(className="card-body", children=[

            html.Div(className="order-grid", children=[

                html.Div(className="form-field", children=[
                    _label("Plant"),
                    _field_input("order-plant", "e.g.  P01"),
                ]),

                html.Div(className="form-field", children=[
                    _label("Part Number"),
                    _field_input("order-part", "e.g.  BM-1234", debounce=True),
                ]),

                html.Div(className="form-field", children=[
                    _label("Unit Price (auto)"),
                    _display("order-price"),
                ]),

                html.Div(className="form-field", children=[
                    _label("Quantity"),
                    _field_input("order-qty", "0", type_="number"),
                ]),

                html.Div(className="form-field form-field-full", children=[
                    _label("Estimated Value"),
                    _display("order-value"),
                ]),

            ]),

            html.Div(className="form-actions", children=[
                html.Button("Submit Order  →", id="order-submit", className="btn-submit"),
                html.Button("Clear",          id="order-clear",  className="btn-clear"),
            ]),

            html.Div(id="order-msg"),

        ]),
    ]),
])


# ── BATCH ORDER TAB ────────────────────────────────────────────

def _batch_row(i):
    return html.Div(className="batch-row", children=[
        html.Div(className="batch-row-num", children=[str(i + 1)]),
        dcc.Input(id=f"batch-plant-{i}", placeholder="Plant",      className="field-input", style={"width": "100%"}),
        dcc.Input(id=f"batch-part-{i}",  placeholder="Part No",    className="field-input", style={"width": "100%"}),
        dcc.Input(id=f"batch-qty-{i}",   placeholder="Qty",        className="field-input", type="number", style={"width": "100%"}),
    ])


batch_tab = html.Div(className="page-body", children=[

    html.Div(className="page-title", children=["📦  Batch Production Order"]),

    html.Div(className="card", children=[
        html.Div("Order Items", className="card-header"),
        html.Div(className="card-body", children=[

            # Column headers
            html.Div(className="batch-header-row", children=[
                html.Div("#",         className="batch-col-label", style={"textAlign": "center"}),
                html.Div("Plant",     className="batch-col-label"),
                html.Div("Part No",   className="batch-col-label"),
                html.Div("Quantity",  className="batch-col-label"),
            ]),

            # 5 fixed rows
            *[_batch_row(i) for i in range(5)],

            # Total row
            html.Div(className="batch-total-row", children=[
                html.Div("Estimated Total", className="batch-total-label"),
                html.Div("—", id="batch-total", className="batch-total-amount"),
            ]),

            html.Div(className="form-actions", style={"marginTop": "18px"}, children=[
                html.Button("Submit Batch  →", id="batch-submit", className="btn-submit"),
            ]),

            html.Div(id="batch-msg"),
        ]),
    ]),
])


# ── ORDER HISTORY TAB ──────────────────────────────────────────

history_tab = html.Div(className="page-body", children=[

    html.Div(className="page-title", children=["📋  Order History"]),

    html.Div(className="card", children=[
        html.Div(className="card-header", children=[
            html.Span("All Orders"),
            html.Span(id="history-count", style={"fontSize": "12px", "fontWeight": "400", "color": "#64748b"}),
        ]),
        html.Div(className="card-body", children=[

            dash_table.DataTable(
                id="history-table",
                columns=[
                    {"name": "ID",          "id": "ID"},
                    {"name": "Plant",       "id": "Plant"},
                    {"name": "Part No",     "id": "Part No"},
                    {"name": "Qty",         "id": "Quantity"},
                    {"name": "Unit Price",  "id": "Unit Price"},
                    {"name": "Value",       "id": "Value"},
                    {"name": "Status",      "id": "Status"},
                    {"name": "Batch",       "id": "batch_id"},
                    {"name": "Approved By", "id": "Approved By"},
                    {"name": "Approved At", "id": "Approved At"},
                ],
                data=[],
                page_size=15,
                sort_action="native",
                filter_action="native",
                style_table={"overflowX": "auto"},
                style_cell={"textAlign": "left", "fontFamily": "Inter, sans-serif",
                             "fontSize": "13px", "padding": "10px 14px"},
                style_header={
                    "background": "#f8fafc", "fontWeight": "600", "fontSize": "11px",
                    "textTransform": "uppercase", "letterSpacing": "0.4px",
                    "color": "#64748b", "borderBottom": "2px solid #e0e4ea",
                },
                style_data={"borderBottom": "1px solid #f0f2f5"},
                style_data_conditional=[
                    {"if": {"filter_query": '{Status} = "PENDING"',  "column_id": "Status"},
                     "color": "#ed6c02", "fontWeight": "700"},
                    {"if": {"filter_query": '{Status} = "APPROVED"', "column_id": "Status"},
                     "color": "#2e7d32", "fontWeight": "700"},
                    {"if": {"filter_query": '{Status} = "REJECTED"', "column_id": "Status"},
                     "color": "#c62828", "fontWeight": "700"},
                    {"if": {"row_index": "odd"}, "backgroundColor": "#fafbfc"},
                ],
                style_as_list_view=True,
            ),
        ]),
    ]),
])


# ── MAIN APP SHELL ─────────────────────────────────────────────

main_app = html.Div(
    id="main-app",
    className="app-wrapper",
    style={"display": "none"},
    children=[

        # Header
        html.Div(className="app-header", children=[
            html.Div(className="header-left", children=[
                html.Span("🏭", className="header-logo"),
                html.Span("Bull Machines", className="header-title"),
                html.Div(className="header-divider"),
                html.Span("Manual Production Orders", className="header-subtitle"),
            ]),
            html.Div(className="header-right", children=[
                html.Span(id="header-user", className="header-user"),
                html.Button("Logout", id="logout-btn", className="btn-logout"),
            ]),
        ]),

        # Tab navigation + inline content (all tabs pre-rendered; Dash hides inactive)
        dcc.Tabs(
            id="app-tabs",
            value="dashboard",
            className="custom-tabs",
            colors={"border": "#e0e4ea", "primary": "#1a3c5e", "background": "#fff"},
            children=[
                dcc.Tab(label="📊  Dashboard",   value="dashboard",
                        style={"fontFamily": "Inter, sans-serif", "padding": "14px 22px", "fontSize": "13px"},
                        selected_style={"fontFamily": "Inter, sans-serif", "padding": "14px 22px",
                                        "fontSize": "13px", "fontWeight": "600", "borderTop": "3px solid #1a3c5e",
                                        "color": "#1a3c5e"},
                        children=[dashboard_tab]),
                dcc.Tab(label="➕  New Order",   value="new-order",
                        style={"fontFamily": "Inter, sans-serif", "padding": "14px 22px", "fontSize": "13px"},
                        selected_style={"fontFamily": "Inter, sans-serif", "padding": "14px 22px",
                                        "fontSize": "13px", "fontWeight": "600", "borderTop": "3px solid #1a3c5e",
                                        "color": "#1a3c5e"},
                        children=[new_order_tab]),
                dcc.Tab(label="📦  Batch Order", value="batch",
                        style={"fontFamily": "Inter, sans-serif", "padding": "14px 22px", "fontSize": "13px"},
                        selected_style={"fontFamily": "Inter, sans-serif", "padding": "14px 22px",
                                        "fontSize": "13px", "fontWeight": "600", "borderTop": "3px solid #1a3c5e",
                                        "color": "#1a3c5e"},
                        children=[batch_tab]),
                dcc.Tab(label="📋  History",     value="history",
                        style={"fontFamily": "Inter, sans-serif", "padding": "14px 22px", "fontSize": "13px"},
                        selected_style={"fontFamily": "Inter, sans-serif", "padding": "14px 22px",
                                        "fontSize": "13px", "fontWeight": "600", "borderTop": "3px solid #1a3c5e",
                                        "color": "#1a3c5e"},
                        children=[history_tab]),
            ],
        ),
    ],
)


# ── ROOT LAYOUT ────────────────────────────────────────────────

layout = html.Div([
    dcc.Store(id="store-user"),
    dcc.Store(id="store-orders", data=[]),
    login_page,
    main_app,
])
