# dal.py
import pymysql
import bcrypt
from config import DB_CONFIG
from typing import List, Dict, Optional, Tuple

def get_connection():
    return pymysql.connect(**DB_CONFIG)

def get_like_status(from_id: str, to_id: str) -> str:
    """获取点赞状态（在模板中使用）"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT status FROM likes 
                WHERE from_student_id = %s AND to_student_id = %s
            """, (from_id, to_id))
            result = cur.fetchone()
            return result[0] if result else 'unliked'

def authenticate_user(user_id: str, password: str) -> Optional[Dict]:
    """
    验证用户身份（支持明文和bcrypt混合）
    """
    with get_connection() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # 先查 user 表
            cur.execute("""
                SELECT user_id, role, password_hash 
                FROM user 
                WHERE user_id = %s AND is_active = 1
            """, (user_id,))
            user = cur.fetchone()
            
            if not user:
                return None
            
            stored_password = user['password_hash']
            
            # 检查是否是 bcrypt 格式（以 $2b$ 开头）
            if stored_password.startswith('$2b$'):
                # 是 bcrypt 格式，使用 checkpw 验证
                try:
                    if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                        return None
                except Exception:
                    return None
            else:
                # 是明文格式，直接比较
                if stored_password != password:
                    return None
            
            # ✅ 确保返回格式正确
            return {
                'user_id': user['user_id'],
                'role': user['role']
            }

# 👤 获取学生数据（用于主页/匹配）
def get_student(student_id: str) -> Optional[Dict]:
    """获取学生基本信息（含新字段）"""
    with get_connection() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # 移除了对 preference 表的 LEFT JOIN
            cur.execute("""
                SELECT s.*
                FROM student s
                WHERE s.student_id = %s AND s.is_active = 1
            """, (student_id,))
            result = cur.fetchone()
            
            if result and result['personal_photos']:
                # 解析 JSON 字段
                import json
                try:
                    result['personal_photos'] = json.loads(result['personal_photos'])
                except:
                    result['personal_photos'] = []
            
            return result
# 👥 获取学生兴趣
def get_student_interests(student_id: str) -> List[Dict]:
    with get_connection() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("""
                SELECT it.tag_id, it.tag_name, it.category
                FROM student_interest si
                JOIN interest_tag it ON si.tag_id = it.tag_id
                WHERE si.student_id = %s AND it.is_active = 1
                ORDER BY it.category, it.tag_name
            """, (student_id,))
            return cur.fetchall()


# 🎉 获取匹配成功列表
def get_mutual_matches(student_id: str) -> List[Dict]:
    with get_connection() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("""
                SELECT 
                    CASE WHEN student_a = %s THEN student_b ELSE student_a END AS matched_id,
                    s.name, s.nickname, s.avatar_url, mr.matched_at
                FROM match_record mr
                JOIN student s ON s.student_id = 
                    CASE WHEN student_a = %s THEN student_b ELSE student_a END
                WHERE (student_a = %s OR student_b = %s)
                  AND mr.matched_at IS NOT NULL
                ORDER BY mr.matched_at DESC
            """, (student_id, student_id, student_id, student_id))
            return cur.fetchall()
        

def send_invitation(from_id: str, to_id: str) -> bool:
    """发送邀约"""
    if from_id == to_id:
        return False
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO invitations (from_student_id, to_student_id)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE
                        status = 'pending',
                        updated_at = NOW()
                """, (from_id, to_id))
                return True
            except Exception as e:
                print(f"[DAL ERROR] send_invitation failed: {e}")
                return False

def respond_to_invitation(invitation_id: int, response: str) -> bool:
    """响应邀约（接受/拒绝）"""
    if response not in ['accepted', 'rejected']:
        return False
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    UPDATE invitations
                    SET status = %s, updated_at = NOW()
                    WHERE id = %s AND status = 'pending'
                """, (response, invitation_id))
                return cur.rowcount > 0
            except Exception as e:
                print(f"[DAL ERROR] respond_to_invitation failed: {e}")
                return False

def send_report(reporter_id: str, reported_id: str, reason: str, description: str = None) -> bool:
    """发送举报"""
    if reporter_id == reported_id:
        return False
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO reports (reporter_id, reported_id, reason, description)
                    VALUES (%s, %s, %s, %s)
                """, (reporter_id, reported_id, reason, description))
                return True
            except Exception as e:
                print(f"[DAL ERROR] send_report failed: {e}")
                return False

def get_invitations(student_id: str, status: str = None) -> List[Dict]:
    """获取邀约列表（作为发起方）"""
    with get_connection() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            sql = """
                SELECT i.*, s.name as to_name, s.nickname as to_nickname, s.wechat_id as to_wechat_id
                FROM invitations i
                JOIN student s ON i.to_student_id = s.student_id
                WHERE i.from_student_id = %s
            """
            params = [student_id]
            
            if status:
                sql += " AND i.status = %s"
                params.append(status)
            
            sql += " ORDER BY i.created_at DESC"
            
            cur.execute(sql, params)
            return cur.fetchall()

def get_received_invitations(student_id: str, status: str = None) -> List[Dict]:
    """获取收到的邀约列表（作为接收方）"""
    with get_connection() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            sql = """
                SELECT i.*, s.name as from_name, s.nickname as from_nickname, s.wechat_id
                FROM invitations i
                JOIN student s ON i.from_student_id = s.student_id
                WHERE i.to_student_id = %s
            """
            params = [student_id]
            
            if status:
                sql += " AND i.status = %s"
                params.append(status)
            
            sql += " ORDER BY i.created_at DESC"
            
            cur.execute(sql, params)
            return cur.fetchall()

def toggle_like(from_id: str, to_id: str) -> bool:
    """切换点赞状态（点赞/取消）"""
    if from_id == to_id:
        return False
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                # 检查是否已存在记录
                cur.execute("""
                    SELECT status FROM likes 
                    WHERE from_student_id = %s AND to_student_id = %s
                """, (from_id, to_id))
                existing = cur.fetchone()
                
                if existing:
                    # 如果已存在，切换状态
                    new_status = 'unliked' if existing[0] == 'liked' else 'liked'
                    cur.execute("""
                        UPDATE likes 
                        SET status = %s, updated_at = NOW()
                        WHERE from_student_id = %s AND to_student_id = %s
                    """, (new_status, from_id, to_id))
                else:
                    # 如果不存在，创建新的点赞记录
                    cur.execute("""
                        INSERT INTO likes (from_student_id, to_student_id, status)
                        VALUES (%s, %s, 'liked')
                    """, (from_id, to_id))
                
                return True
            except Exception as e:
                print(f"[DAL ERROR] toggle_like failed: {e}")
                return False

def get_like_status(from_id: str, to_id: str) -> str:
    """获取点赞状态"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT status FROM likes 
                WHERE from_student_id = %s AND to_student_id = %s
            """, (from_id, to_id))
            result = cur.fetchone()
            return result[0] if result else 'unliked'

def get_like_count(student_id: str) -> int:
    """获取某用户被点赞的次数"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as count 
                FROM likes 
                WHERE to_student_id = %s AND status = 'liked'
            """, (student_id,))
            result = cur.fetchone()
            return result[0] if result else 0

def get_user_likes(student_id: str) -> List[Dict]:
    """获取用户点赞的列表"""
    with get_connection() as conn:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("""
                SELECT l.*, s.name as to_name, s.nickname as to_nickname
                FROM likes l
                JOIN student s ON l.to_student_id = s.student_id
                WHERE l.from_student_id = %s AND l.status = 'liked'
                ORDER BY l.created_at DESC
            """, (student_id,))
            return cur.fetchall()
