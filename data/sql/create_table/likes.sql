CREATE TABLE likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    from_student_id VARCHAR(20) NOT NULL,
    to_student_id VARCHAR(20) NOT NULL,
    status ENUM('liked', 'unliked') DEFAULT 'liked',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (from_student_id) REFERENCES user(user_id),
    FOREIGN KEY (to_student_id) REFERENCES user(user_id),
    UNIQUE KEY unique_like (from_student_id, to_student_id),
    INDEX idx_from_student (from_student_id),
    INDEX idx_to_student (to_student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;