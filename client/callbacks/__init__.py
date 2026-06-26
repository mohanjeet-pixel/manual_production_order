from client.callbacks import auth, orders


def register(app):
    auth.register(app)
    orders.register(app)
