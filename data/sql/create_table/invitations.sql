DROP TABLE IF EXISTS invitations;

CREATE TABLE invitations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    from_student_id VARCHAR(20) NOT NULL,
    to_student_id VARCHAR(20) NOT NULL,
    status ENUM('pending', 'accepted', 'rejected', 'cancelled') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (from_student_id) REFERENCES user(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (to_student_id) REFERENCES user(user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY unique_invitation (from_student_id, to_student_id),
    INDEX idx_from_student (from_student_id),
    INDEX idx_to_student (to_student_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;