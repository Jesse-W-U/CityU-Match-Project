DROP TABLE IF EXISTS student_interest;

CREATE TABLE student_interest (
    student_id CHAR(8) NOT NULL,
    tag_id SMALLINT UNSIGNED NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, tag_id),
    FOREIGN KEY (student_id) REFERENCES student(student_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES interest_tag(tag_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_student_id (student_id),
    INDEX idx_tag_id (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;