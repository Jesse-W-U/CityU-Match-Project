# pages/profile.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from dal import get_student, get_student_interests, get_connection
import bcrypt
from dal import authenticate_user

bp = Blueprint('profile', __name__, url_prefix='/user')

@bp.route('/<student_id>')
def view_profile(student_id):
    student = get_student(student_id)
    if not student:
        return "Student not found", 404
    
    interests = get_student_interests(student_id)
    
    return render_template('profile.html', 
                         student=student, 
                         interests=interests)

# pages/profile.py
@bp.route('/<student_id>/settings')
def settings(student_id):
    return redirect(url_for('profile.edit_profile', student_id=student_id))

@bp.route('/<student_id>/settings/edit', methods=['GET', 'POST'])
def edit_profile(student_id):
    student = get_student(student_id)
    if not student:
        return "Student not found", 404
    
    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        gender = request.form.get('gender', '')
        college = request.form.get('college', '')
        major = request.form.get('major', '').strip()
        year_of_study = int(request.form.get('year_of_study', 1))
        identity = request.form.get('identity', '')
        email = request.form.get('email', '').strip()
        wechat_id = request.form.get('wechat_id', '').strip()
        
        birth_date = request.form.get('birth_date', '')
        height = request.form.get('height', type=float)
        weight = request.form.get('weight', type=float)
        hometown = request.form.get('hometown', '').strip()
        marital_status = request.form.get('marital_status', '')
        bio = request.form.get('bio', '').strip()
        ideal_partner = request.form.get('ideal_partner', '').strip()
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                sql = """
                    UPDATE student 
                    SET nickname = %s, gender = %s, college = %s, major = %s, 
                        year_of_study = %s, identity = %s, email = %s, wechat_id = %s,
                        birth_date = %s, height = %s, weight = %s, hometown = %s,
                        marital_status = %s, bio = %s, ideal_partner = %s, updated_at = NOW()
                    WHERE student_id = %s
                """
                params = [
                    nickname, gender, college, major, year_of_study, identity, email, wechat_id,
                    birth_date if birth_date else None,
                    height if height else None,
                    weight if weight else None,
                    hometown if hometown else None,
                    marital_status if marital_status else None,
                    bio if bio else None,
                    ideal_partner if ideal_partner else None,
                    student_id
                ]
                cur.execute(sql, params)
        
        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile.edit_profile', student_id=student_id))
    
    return render_template('settings/edit.html', student=student)

@bp.route('/<student_id>/settings/password', methods=['GET', 'POST'])
def change_password(student_id):
    student = get_student(student_id)
    if not student:
        return "Student not found", 404
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        user = authenticate_user(student_id, current_password)
        if not user:
            flash("Current password is incorrect", "danger")
            return redirect(url_for('profile.change_password', student_id=student_id))
        
        if len(new_password) < 6:
            flash("New password must be at least 6 characters", "danger")
            return redirect(url_for('profile.change_password', student_id=student_id))
        
        if new_password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for('profile.change_password', student_id=student_id))
        
        hashed_password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user 
                    SET password_hash = %s, updated_at = NOW()
                    WHERE user_id = %s
                """, (hashed_password.decode(), student_id))
        
        flash("Password changed successfully!", "success")
        return redirect(url_for('profile.change_password', student_id=student_id))
    
    return render_template('settings/password.html', student=student)

@bp.route('/')
def user_home():
    if session.get('user_id'):
        return redirect(url_for('profile.view_profile', student_id=session['user_id']))
    else:
        return redirect(url_for('login.login_form'))