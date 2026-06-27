from client.callbacks import auth, orders, batch, dashboard


def register(app):
    auth.register(app)
    dashboard.register(app)
    orders.register(app)
    batch.register(app)
