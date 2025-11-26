# app.py
from flask import Flask, session, redirect, url_for
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(24).hex()

    # 添加模板全局函数
    from dal import get_like_status
    app.jinja_env.globals['get_like_status'] = get_like_status

    # 注册蓝图
    from pages import login, profile, matching, admin
    app.register_blueprint(login.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(matching.bp)
    app.register_blueprint(admin.bp)
    
    # 根路径重定向到登录页
    @app.route('/')
    def index():
        return redirect(url_for('login.login_form'))
    
    # 登出路由
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login.login_form'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)