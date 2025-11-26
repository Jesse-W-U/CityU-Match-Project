DROP TABLE IF EXISTS user;

CREATE TABLE user (
    user_id VARCHAR(20) NOT NULL PRIMARY KEY COMMENT '登录ID: 学号 或 "admin"',
    password_hash VARCHAR(255) NOT NULL COMMENT 'bcrypt哈希',
    role ENUM('student', 'admin') NOT NULL COMMENT '角色',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_role (role),
    INDEX idx_user_id_role (user_id, role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;