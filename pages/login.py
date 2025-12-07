# pages/login.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from dal import get_connection, authenticate_user
import bcrypt

bp = Blueprint('login', __name__)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not student_id or not password or not confirm_password:
            flash("All fields are required", "danger")
            return redirect(url_for('login.register'))
        
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for('login.register'))
        
        if len(password) < 6:
            flash("Password must be at least 6 characters", "danger")
            return redirect(url_for('login.register'))
        
        if not student_id.startswith('58') or len(student_id) != 8 or not student_id.isdigit():
            flash("Invalid student ID format (must be 8 digits starting with 58)", "danger")
            return redirect(url_for('login.register'))
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id FROM user WHERE user_id = %s", (student_id,))
                if cur.fetchone():
                    flash("Student ID already exists", "danger")
                    return redirect(url_for('login.register'))
        
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute("""
                        INSERT INTO user (user_id, password_hash, role, is_active)
                        VALUES (%s, %s, 'student', 1)
                    """, (student_id, hashed_password.decode()))
                    
                    cur.execute("""
                        INSERT INTO student (
                            student_id, name, nickname, gender, college, year_of_study,
                            major, email, wechat_id, bio, is_verified, is_active
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 1)
                    """, (
                        student_id,
                        request.form.get('name', '').strip(),
                        request.form.get('nickname', '').strip(),
                        request.form.get('gender', ''),
                        request.form.get('college', ''),
                        int(request.form.get('year_of_study', 1)),
                        request.form.get('major', '').strip(),
                        request.form.get('email', '').strip(),
                        request.form.get('wechat_id', '').strip(),
                        request.form.get('bio', '').strip()
                    ))
                    
                    selected_tags = request.form.getlist('interests')
                    if selected_tags:
                        for tag_id in selected_tags:
                            cur.execute("""
                                INSERT INTO student_interest (student_id, tag_id, created_at)
                                VALUES (%s, %s, NOW())
                            """, (student_id, tag_id))
                    
                    flash("Registration successful! Please log in.", "success")
                    return redirect(url_for('login.login_form'))
                    
                except Exception as e:
                    flash(f"Registration failed: {str(e)}", "danger")
                    return redirect(url_for('login.register'))
    
    all_tags = []
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT tag_id, tag_name, category FROM interest_tag WHERE is_active = 1 ORDER BY category, tag_name")
            raw_tags = cur.fetchall()
            all_tags = [
                {
                    'tag_id': tag[0],      # tag_id
                    'tag_name': tag[1],    # tag_name  
                    'category': tag[2]     # category
                }
                for tag in raw_tags
            ]
    
    return render_template('register.html', all_tags=all_tags)


@bp.route('/login', methods=['GET', 'POST'])
def login_form():
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip() or request.form.get('user_id', '').strip()
        password = request.form.get('password', '')
        
        print(f"DEBUG: Attempting login with student_id: {student_id}")
        
        user = authenticate_user(student_id, password)
        if user:
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('profile.view_profile', student_id=user['user_id']))
        else:
            flash("Invalid student ID or password", "danger")
            return redirect(url_for('login.login_form'))
    
    error = request.args.get('error')
    return render_template('login.html', error=error)