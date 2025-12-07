# pages/matching.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from dal import get_connection, get_student, get_student_interests, send_invitation, send_report, get_invitations, get_received_invitations, get_like_status, toggle_like, get_like_count
import pymysql

bp = Blueprint('matching', __name__, url_prefix='/matching')

@bp.route('/search')
def search_matches():
    college = request.args.get('college', '')
    identity = request.args.get('identity', '')
    age_min = request.args.get('age_min', type=int)
    age_max = request.args.get('age_max', type=int)
    major = request.args.get('major', '')
    hometown = request.args.get('hometown', '')
    mbti = request.args.get('mbti', '')
    gender = request.args.get('gender', '')
    
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page
    
    students = []
    total_count = 0
    
    with get_connection() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            count_sql = """
                SELECT COUNT(DISTINCT s.student_id) as total
                FROM student s
            """
            count_params = []
            
            if mbti:
                count_sql += """
                    JOIN student_interest si ON s.student_id = si.student_id
                    JOIN interest_tag it ON si.tag_id = it.tag_id
                """
            
            count_sql += " WHERE s.is_active = 1 AND s.student_id != %s"
            count_params.append(session['user_id'])
            
            if college:
                count_sql += " AND s.college = %s"
                count_params.append(college)
            if identity:
                count_sql += " AND s.identity = %s"
                count_params.append(identity)
            if major:
                count_sql += " AND s.major = %s"
                count_params.append(major)
            if hometown:
                count_sql += " AND s.hometown = %s"
                count_params.append(hometown)
            if gender:
                count_sql += " AND s.gender = %s"
                count_params.append(gender)
            if mbti:
                count_sql += " AND it.tag_name = %s AND it.category = 'MBTI'"
                count_params.append(mbti)
            
            if age_min:
                count_sql += " AND (YEAR(CURDATE()) - YEAR(s.birth_date)) >= %s"
                count_params.append(age_min)
            if age_max:
                count_sql += " AND (YEAR(CURDATE()) - YEAR(s.birth_date)) <= %s"
                count_params.append(age_max)
            
            cur.execute(count_sql, count_params)
            total_count = cur.fetchone()['total']
            
            sql = """
                SELECT s.*
                FROM student s
            """
            
            if mbti:
                sql += """
                    JOIN student_interest si ON s.student_id = si.student_id
                    JOIN interest_tag it ON si.tag_id = it.tag_id
                """
            
            sql += " WHERE s.is_active = 1 AND s.student_id != %s"
            params = [session['user_id']]
            
            if college:
                sql += " AND s.college = %s"
                params.append(college)
            if identity:
                sql += " AND s.identity = %s"
                params.append(identity)
            if major:
                sql += " AND s.major = %s"
                params.append(major)
            if hometown:
                sql += " AND s.hometown = %s"
                params.append(hometown)
            if gender:
                sql += " AND s.gender = %s"
                params.append(gender)
            if mbti:
                sql += " AND it.tag_name = %s AND it.category = 'MBTI'"
                params.append(mbti)
            
            if age_min:
                sql += " AND (YEAR(CURDATE()) - YEAR(s.birth_date)) >= %s"
                params.append(age_min)
            if age_max:
                sql += " AND (YEAR(CURDATE()) - YEAR(s.birth_date)) <= %s"
                params.append(age_max)
            
            sql += " ORDER BY s.updated_at DESC LIMIT %s OFFSET %s"
            params.extend([per_page, offset])
            
            cur.execute(sql, params)
            students = cur.fetchall()
    
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return render_template('matching/search.html', 
                         students=students,
                         filters={
                             'college': college,
                             'identity': identity,
                             'age_min': age_min,
                             'age_max': age_max,
                             'major': major,
                             'hometown': hometown,
                             'mbti': mbti,
                             'gender': gender
                         },
                         pagination={
                             'page': page,
                             'total_pages': total_pages,
                             'has_prev': has_prev,
                             'has_next': has_next,
                             'total_count': total_count
                         })

@bp.route('/detail/<student_id>')
def student_detail(student_id):
    student = get_student(student_id)
    if not student:
        return "Student not found", 404
    
    interests = get_student_interests(student_id)
    like_count = get_like_count(student_id)
    
    return render_template('matching/detail.html', 
                         student=student, 
                         interests=interests,
                         like_count=like_count)

@bp.route('/like/<target_id>', methods=['POST'])
def like_student(target_id):
    current_user_id = session.get('user_id')
    if not current_user_id:
        flash("Please login first", "danger")
        return redirect(url_for('login.login_form'))
    
    if current_user_id == target_id:
        flash("You cannot like yourself", "warning")
        return redirect(url_for('matching.student_detail', student_id=target_id))
    
    success = toggle_like(current_user_id, target_id)
    if success:
        status = get_like_status(current_user_id, target_id)
        if status == 'liked':
            flash("Liked successfully!", "success")
        else:
            flash("Unliked successfully!", "info")
    else:
        flash("Operation failed", "danger")
    
    return redirect(url_for('matching.student_detail', student_id=target_id))

@bp.route('/invite/<target_id>', methods=['POST'])
def send_invitation_to(target_id):
    current_user_id = session.get('user_id')
    if not current_user_id:
        flash("Please login first", "danger")
        return redirect(url_for('login.login_form'))
    
    if current_user_id == target_id:
        flash("You cannot invite yourself", "warning")
        return redirect(url_for('matching.student_detail', student_id=target_id))
    
    success = send_invitation(current_user_id, target_id)
    if success:
        flash("Invitation sent successfully!", "success")
    else:
        flash("Failed to send invitation", "danger")
    
    return redirect(url_for('matching.student_detail', student_id=target_id))

@bp.route('/history')
def invitation_history():
    current_user_id = session.get('user_id')
    if not current_user_id:
        return redirect(url_for('login.login_form'))
    
    sent_invitations = get_invitations(current_user_id)
    
    received_invitations = get_received_invitations(current_user_id)
    
    return render_template('matching/history.html',
                         sent_invitations=sent_invitations,
                         received_invitations=received_invitations)

@bp.route('/respond-invitation/<int:invitation_id>/<response>', methods=['GET'])
def respond_invitation(invitation_id: int, response: str):
    current_user_id = session.get('user_id')
    if not current_user_id:
        flash("Please login first", "danger")
        return redirect(url_for('login.login_form'))
    
    if response not in ['accepted', 'rejected']:
        flash("Invalid response", "danger")
        return redirect(url_for('matching.invitation_history'))
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM invitations 
                WHERE id = %s AND to_student_id = %s AND status = 'pending'
            """, (invitation_id, current_user_id))
            invitation = cur.fetchone()
            
            if not invitation:
                flash("Invitation not found or already responded", "danger")
                return redirect(url_for('matching.invitation_history'))
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    UPDATE invitations
                    SET status = %s, updated_at = NOW()
                    WHERE id = %s AND to_student_id = %s
                """, (response, invitation_id, current_user_id))
                
                if cur.rowcount > 0:
                    if response == 'accepted':
                        flash("Invitation accepted successfully!", "success")
                    else:
                        flash("Invitation rejected successfully!", "info")
                else:
                    flash("Failed to update invitation", "danger")
            except Exception as e:
                flash("Operation failed", "danger")
    
    return redirect(url_for('matching.invitation_history'))

@bp.route('/report/<target_id>', methods=['POST'])
def report_student(target_id):
    current_user_id = session.get('user_id')
    if not current_user_id:
        flash("Please login first", "danger")
        return redirect(url_for('login.login_form'))
    
    if current_user_id == target_id:
        flash("You cannot report yourself", "warning")
        return redirect(url_for('matching.student_detail', student_id=target_id))
    
    reason = request.form.get('reason', '')
    description = request.form.get('description', '')
    
    if not reason:
        flash("Please select a reason", "danger")
        return redirect(url_for('matching.student_detail', student_id=target_id))
    
    success = send_report(current_user_id, target_id, reason, description)
    if success:
        flash("Report submitted successfully!", "success")
    else:
        flash("Failed to submit report", "danger")
    
    return redirect(url_for('matching.student_detail', student_id=target_id))