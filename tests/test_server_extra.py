import json
from pathlib import Path
import pytest

import server
from server import app, get_db


def test_health_endpoint():
    client = app.test_client()
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'ok'
    assert data['database'] == 'ok'


def test_metrics_endpoint():
    client = app.test_client()
    resp = client.get('/metrics')
    assert resp.status_code == 200
    # should return bytes text for prometheus metrics
    assert resp.data is not None and len(resp.data) > 0


def test_index_requires_login():
    client = app.test_client()
    resp = client.get('/index')
    # should redirect to login when not authenticated
    assert resp.status_code in (302, 301)


def test_signup_logout_and_login_flow():
    client = app.test_client()

    # signup creates a user and redirects to index
    signup_resp = client.post('/signup', data={'username': 'eve', 'password': 'pw'}, follow_redirects=True)
    assert signup_resp.status_code == 200

    # logout should clear session and redirect to landing
    logout_resp = client.get('/logout', follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b"SIENE" in logout_resp.data

    # login with correct credentials should succeed and redirect to /index
    login_resp = client.post('/login', data={'username': 'eve', 'password': 'pw'}, follow_redirects=True)
    assert login_resp.status_code == 200


def test_account_update_and_delete():
    client = app.test_client()

    # create user by signing up
    client.post('/signup', data={'username': 'carol', 'password': 'initial'}, follow_redirects=True)

    # update username
    resp = client.post('/account', data={'action': 'update_username', 'username': 'carol2'}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Username updated.' in resp.data

    # update password (wrong current password)
    resp2 = client.post('/account', data={'action': 'update_password', 'current_password': 'wrong', 'new_password': 'x', 'confirm_password': 'x'}, follow_redirects=True)
    assert b'Current password is incorrect.' in resp2.data

    # correct current password
    resp3 = client.post('/account', data={'action': 'update_password', 'current_password': 'initial', 'new_password': 'newpass', 'confirm_password': 'newpass'}, follow_redirects=True)
    assert b'Password updated.' in resp3.data

    # attempt delete without typing DELETE
    resp4 = client.post('/account', data={'action': 'delete_account', 'confirm': 'nope'}, follow_redirects=True)
    assert b'Type DELETE in the confirmation' in resp4.data

    # delete with correct confirmation
    resp5 = client.post('/account', data={'action': 'delete_account', 'confirm': 'DELETE'}, follow_redirects=True)
    assert resp5.status_code == 200
    # after deletion, landing page should be shown
    assert b'SIENE' in resp5.data

    # confirm user removed from DB
    with app.app_context():
        db = get_db()
        rows = db.execute('SELECT id FROM users WHERE username = ?', ('carol2',)).fetchall()
        assert len(rows) == 0
