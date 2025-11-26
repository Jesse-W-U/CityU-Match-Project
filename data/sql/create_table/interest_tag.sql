DROP TABLE IF EXISTS interest_tag;

CREATE TABLE interest_tag (
    tag_id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    tag_name VARCHAR(50) NOT NULL UNIQUE COMMENT '标签名',
    category ENUM('MBTI', 'Personality', 'Hobby', 'Lifestyle', 'Zodiac') NOT NULL COMMENT '标签类别',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_tag_name (tag_name),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;