DROP TABLE IF EXISTS student;

CREATE TABLE student (
    student_id CHAR(8) NOT NULL PRIMARY KEY COMMENT 'Student ID, e.g., 58123456',
    name VARCHAR(50) NOT NULL COMMENT 'Real name (displayed as nickname for privacy)',
    nickname VARCHAR(30) DEFAULT NULL COMMENT 'User-defined nickname',
    gender ENUM('M', 'F', 'X') NOT NULL COMMENT 'M=Male, F=Female, X=Other',
    college ENUM(
        'College of Business', 
        'College of Liberal Arts and Social Sciences',
        'College of Science',
        'College of Engineering',
        'College of Veterinary Medicine and Life Sciences',
        'Jockey Club College of Veterinary Medicine and Life Sciences',
        'Cheng Yu Tung College',
        'Run Run Shaw College',
        'Other'
    ) NOT NULL COMMENT 'College (based on CityU real colleges)',
    year_of_study TINYINT NOT NULL CHECK (year_of_study BETWEEN 1 AND 6) COMMENT 'Year of study (including PhD)',
    major VARCHAR(100) NOT NULL COMMENT 'Full major name',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT 'School email @my.cityu.edu.hk',
    wechat_id VARCHAR(50) DEFAULT NULL COMMENT 'WeChat ID (optional)',
    bio TEXT DEFAULT NULL COMMENT 'Self-introduction (≤500 words)',
    avatar_url VARCHAR(255) DEFAULT NULL COMMENT 'Avatar URL (can be empty)',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Whether student email verification completed',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Whether account is activated',
    
    -- New fields
    birth_date DATE COMMENT 'Birth date',
    height DECIMAL(5,2) COMMENT 'Height (cm)',
    weight DECIMAL(5,2) COMMENT 'Weight (kg)',
    hometown VARCHAR(100) COMMENT 'Hometown',
    marital_status ENUM('Single', 'Divorced-Single', 'Divorced-With-Child', 'Divorced-Without-Child', 'Widowed') COMMENT 'Marital status',
    ideal_partner TEXT COMMENT 'Ideal partner (text)',
    identity ENUM('Undergraduate', 'Graduate', 'PhD') COMMENT 'Identity (Undergraduate, Graduate, PhD)',
    personal_photos JSON NULL COMMENT 'Personal photos (JSON array of URLs)',
    
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_college_gender (college, gender),
    INDEX idx_year (year_of_study),
    INDEX idx_identity (identity),
    INDEX idx_marital_status (marital_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;