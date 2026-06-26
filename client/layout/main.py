from dash import dcc, html, dash_table

layout = html.Div([

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
                    {"name": "ID", "id": "ID"},
                    {"name": "Employee", "id": "Employee"},
                    {"name": "Plant", "id": "Plant"},
                    {"name": "Part No", "id": "Part No"},
                    {"name": "Quantity", "id": "Quantity"},
                    {"name": "Unit Price", "id": "Unit Price"},
                    {"name": "Value", "id": "Value"},
                    {"name": "Status", "id": "Status"},
                    {"name": "Approved By", "id": "Approved By"},
                    {"name": "Approved At", "id": "Approved At"}
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
