# pages/admin.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from functools import wraps
from dal import get_connection

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('login.login_form', error='Admin access required'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@admin_required
def dashboard():
    """管理员仪表盘"""
    stats = {}
    
    with get_connection() as conn:
        with conn.cursor() as cur:  # ✅ 保持普通游标
            # 1. 活跃学生数
            cur.execute("SELECT COUNT(*) FROM user WHERE role = 'student' AND is_active = 1")
            stats['active_students'] = cur.fetchone()[0]
            
            # 2. 管理员数
            cur.execute("SELECT COUNT(*) FROM user WHERE role = 'admin'")
            stats['admin_count'] = cur.fetchone()[0]
            
            # 3. 总兴趣标签数
            cur.execute("SELECT COUNT(*) FROM interest_tag")
            stats['total_tags'] = cur.fetchone()[0]
            
            # 4. 总邀约数
            cur.execute("SELECT COUNT(*) FROM invitations")
            stats['total_invitations'] = cur.fetchone()[0]
            
            # 5. 已接受邀约数
            cur.execute("SELECT COUNT(*) FROM invitations WHERE status = 'accepted'")
            stats['accepted_invitations'] = cur.fetchone()[0]
            
            # 6. 最近注册用户（前10个）
            cur.execute("""
                SELECT u.user_id, u.role, u.is_active, u.created_at,
                       s.name, s.college, s.major
                FROM user u
                LEFT JOIN student s ON u.user_id = s.student_id
                ORDER BY u.created_at DESC
                LIMIT 10
            """)
            stats['recent_users'] = cur.fetchall()
            
            # 7. 热门兴趣标签TOP10（按类别分组）
            cur.execute("""
                SELECT it.tag_name, it.category, COUNT(si.tag_id) AS count
                FROM student_interest si
                JOIN interest_tag it ON si.tag_id = it.tag_id
                GROUP BY it.tag_id
                ORDER BY count DESC
                LIMIT 10
            """)
            stats['top_tags'] = cur.fetchall()  # 返回元组列表: [(name, category, count), ...]
            
            # 8. 被点赞最多的前5名学生
            cur.execute("""
                SELECT s.student_id, s.name, s.nickname, 
                       COALESCE(like_counts.count, 0) as like_count
                FROM student s
                LEFT JOIN (
                    SELECT to_student_id, COUNT(*) as count
                    FROM likes
                    WHERE status = 'liked'
                    GROUP BY to_student_id
                ) like_counts ON s.student_id = like_counts.to_student_id
                WHERE s.is_active = 1
                ORDER BY like_counts.count DESC
                LIMIT 5
            """)
            stats['top_liked_students'] = cur.fetchall()  # 返回元组列表: [(id, name, nickname, count), ...]
    
    return render_template('admin/dashboard.html', stats=stats)


@bp.route('/users')
@bp.route('/users/page/<int:page>')
@admin_required
def user_management(page=1):
    """用户管理页面（带分页）"""
    per_page = 10
    offset = (page - 1) * per_page
    
    users = []
    total_count = 0
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 计算总数
            cur.execute("SELECT COUNT(*) FROM user")
            total_count = cur.fetchone()[0]
            
            # 获取分页数据
            cur.execute("""
                SELECT u.user_id, u.role, u.is_active, u.created_at,
                       s.name, s.college, s.major
                FROM user u
                LEFT JOIN student s ON u.user_id = s.student_id
                ORDER BY u.created_at DESC
                LIMIT %s OFFSET %s
            """, (per_page, offset))
            users = cur.fetchall()
    
    # 计算分页信息
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return render_template('admin/users.html', 
                         users=users,
                         pagination={
                             'page': page,
                             'total_pages': total_pages,
                             'total_count': total_count,
                             'has_prev': has_prev,
                             'has_next': has_next
                         })

@bp.route('/tags', methods=['GET', 'POST'])
@admin_required
def tag_management():
    """兴趣标签管理页面（带筛选和新增功能）"""
    if request.method == 'POST':
        # 处理新增标签
        tag_name = request.form.get('tag_name', '').strip()
        category = request.form.get('category', '').strip()
        
        if tag_name and category:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    try:
                        cur.execute("""
                            INSERT INTO interest_tag (tag_name, category, is_active)
                            VALUES (%s, %s, 1)
                        """, (tag_name, category))
                        flash(f"Tag '{tag_name}' added successfully!", "success")
                    except Exception as e:
                        flash("Failed to add tag", "danger")
        else:
            flash("Tag name and category are required", "danger")
    
    # 获取筛选参数
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    
    tags = []
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 查询标签及其使用次数
            sql = """
                SELECT it.tag_id, it.tag_name, it.category, it.is_active, it.created_at,
                       COALESCE(usage_counts.count, 0) as use_count
                FROM interest_tag it
                LEFT JOIN (
                    SELECT tag_id, COUNT(*) as count
                    FROM student_interest
                    GROUP BY tag_id
                ) usage_counts ON it.tag_id = usage_counts.tag_id
                WHERE 1=1
            """
            params = []
            
            if category_filter:
                sql += " AND it.category = %s"
                params.append(category_filter)
            if status_filter:
                sql += " AND it.is_active = %s"
                params.append(int(status_filter))
            
            sql += " ORDER BY it.category, it.tag_name"
            
            cur.execute(sql, params)
            tags = cur.fetchall()
    
    return render_template('admin/tags.html', 
                         tags=tags,
                         category_filter=category_filter,
                         status_filter=status_filter)

@bp.route('/tags/<int:tag_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_tag_status(tag_id):
    """切换标签状态"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                # 获取当前状态
                cur.execute("SELECT is_active FROM interest_tag WHERE tag_id = %s", (tag_id,))
                result = cur.fetchone()
                
                if result:
                    current_status = result[0]
                    new_status = not current_status
                    
                    cur.execute("""
                        UPDATE interest_tag 
                        SET is_active = %s, updated_at = NOW()
                        WHERE tag_id = %s
                    """, (new_status, tag_id))
                    
                    if new_status:
                        flash(f"Tag enabled successfully!", "success")
                    else:
                        flash(f"Tag disabled successfully!", "info")
                else:
                    flash("Tag not found", "danger")
            except Exception as e:
                flash("Operation failed", "danger")
    
    return redirect(url_for('admin.tag_management'))

@bp.route('/users/<user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """切换用户状态"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                # 获取当前状态
                cur.execute("SELECT is_active FROM user WHERE user_id = %s", (user_id,))
                result = cur.fetchone()
                
                if result:
                    current_status = result[0]
                    new_status = not current_status
                    
                    cur.execute("""
                        UPDATE user 
                        SET is_active = %s, updated_at = NOW()
                        WHERE user_id = %s
                    """, (new_status, user_id))
                    
                    if new_status:
                        flash(f"User {user_id} activated successfully!", "success")
                    else:
                        flash(f"User {user_id} deactivated successfully!", "info")
                else:
                    flash("User not found", "danger")
            except Exception as e:
                flash("Operation failed", "danger")
    
    return redirect(url_for('admin.user_management'))

@bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """编辑用户信息"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 获取用户信息
            cur.execute("""
                SELECT u.user_id, u.role, u.is_active, u.created_at,
                       s.name, s.college, s.major, s.email, s.wechat_id, s.bio
                FROM user u
                LEFT JOIN student s ON u.user_id = s.student_id
                WHERE u.user_id = %s
            """, (user_id,))
            user = cur.fetchone()
            
            if not user:
                flash("User not found", "danger")
                return redirect(url_for('admin.user_management'))
    
    if request.method == 'POST':
        # 更新用户信息
        new_role = request.form.get('role', '')
        new_name = request.form.get('name', '').strip()
        new_college = request.form.get('college', '').strip()
        new_major = request.form.get('major', '').strip()
        new_email = request.form.get('email', '').strip()
        new_wechat = request.form.get('wechat_id', '').strip()
        new_bio = request.form.get('bio', '').strip()
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                try:
                    # 更新用户表（角色）
                    cur.execute("""
                        UPDATE user 
                        SET role = %s, updated_at = NOW()
                        WHERE user_id = %s
                    """, (new_role, user_id))
                    
                    # 如果是学生，更新学生表
                    if new_role == 'student':
                        cur.execute("""
                            UPDATE student 
                            SET name = %s, college = %s, major = %s, 
                                email = %s, wechat_id = %s, bio = %s, updated_at = NOW()
                            WHERE student_id = %s
                        """, (new_name, new_college, new_major, new_email, new_wechat, new_bio, user_id))
                    
                    flash(f"User {user_id} updated successfully!", "success")
                except Exception as e:
                    flash("Update failed", "danger")
        
        return redirect(url_for('admin.user_management'))
    
    return render_template('admin/edit_user.html', user=user)

@bp.route('/reports')
@admin_required
def report_management():
    """举报管理页面"""
    reports = []
    
    with get_connection() as conn:
        with conn.cursor() as cur:  # ✅ 修正：直接使用 dal.py 的游标（已处理 DictCursor）
            cur.execute("""
                SELECT r.*, 
                       s1.name as reporter_name, s1.nickname as reporter_nickname,
                       s2.name as reported_name, s2.nickname as reported_nickname
                FROM reports r
                JOIN student s1 ON r.reporter_id = s1.student_id
                JOIN student s2 ON r.reported_id = s2.student_id
                ORDER BY r.created_at DESC
            """)
            reports = cur.fetchall()
    
    return render_template('admin/reports.html', reports=reports)

@bp.route('/reports/<int:report_id>/resolve', methods=['POST'])
@admin_required
def resolve_report(report_id):
    """处理举报（标记为已解决）"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    UPDATE reports 
                    SET status = 'resolved', resolved_at = NOW()
                    WHERE id = %s
                """, (report_id,))
                
                if cur.rowcount > 0:
                    flash("Report marked as resolved successfully!", "success")
                else:
                    flash("Report not found", "danger")
            except Exception as e:
                flash("Operation failed", "danger")
    
    return redirect(url_for('admin.report_management'))

@bp.route('/reports/<int:report_id>/delete', methods=['POST'])
@admin_required
def delete_report(report_id):
    """删除举报记录"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("DELETE FROM reports WHERE id = %s", (report_id,))
                
                if cur.rowcount > 0:
                    flash("Report deleted successfully!", "success")
                else:
                    flash("Report not found", "danger")
            except Exception as e:
                flash("Operation failed", "danger")
    
    return redirect(url_for('admin.report_management'))

