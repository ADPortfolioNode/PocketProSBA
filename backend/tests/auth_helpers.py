"""Test helpers for routes behind ``auth_required``.

    token = make_token(app)                    # creates a user, signs a token
    authenticate(client, app)                  # every later request is signed in
    client.get(url, headers=auth_header(app))  # one signed-in request
"""
from backend.models.chat import db

TEST_EMAIL = "tester@example.com"
TEST_PASSWORD = "tester-password-1"


def make_user(app, email=TEST_EMAIL, password=TEST_PASSWORD):
    from backend.models.user import User

    with app.app_context():
        db.create_all()
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(email=email, name="Tester")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        return user.id


def make_token(app, email=TEST_EMAIL, password=TEST_PASSWORD, ttl_seconds=None):
    """Sign a real access token for a (created on demand) test user."""
    from backend.app.auth import create_access_token
    from backend.models.user import User

    user_id = make_user(app, email, password)
    with app.app_context():
        user = db.session.get(User, user_id)
        return create_access_token(user, app=app, ttl_seconds=ttl_seconds)["token"]


def auth_header(app, **kw):
    return {"Authorization": f"Bearer {make_token(app, **kw)}"}


def authenticate(client, app=None, **kw):
    """Send a valid bearer token on every request this test client makes."""
    app = app or client.application
    token = make_token(app, **kw)
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return token
