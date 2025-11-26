CREATE TABLE reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reporter_id VARCHAR(20) NOT NULL,
    reported_id VARCHAR(20) NOT NULL,
    reason VARCHAR(255) NOT NULL,
    description TEXT,
    status ENUM('pending', 'reviewed', 'resolved') DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL,
    FOREIGN KEY (reporter_id) REFERENCES user(user_id),
    FOREIGN KEY (reported_id) REFERENCES user(user_id),
    INDEX idx_reporter (reporter_id),
    INDEX idx_reported (reported_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;