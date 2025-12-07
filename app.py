# app.py
from flask import Flask, session, redirect, url_for
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(24).hex()

    from dal import get_like_status
    app.jinja_env.globals['get_like_status'] = get_like_status

    from pages import login, profile, matching, admin
    app.register_blueprint(login.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(matching.bp)
    app.register_blueprint(admin.bp)
    
    @app.route('/')
    def index():
        return redirect(url_for('login.login_form'))
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login.login_form'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)