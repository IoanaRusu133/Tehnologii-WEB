CREATE DATABASE IF NOT EXISTS theater_crawler
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
USE theater_crawler;
CREATE TABLE IF NOT EXISTS shows (
id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
title VARCHAR(255) NOT NULL,
author VARCHAR(255) NULL,
director VARCHAR(255) NULL,
description TEXT NULL,
genre VARCHAR(255) NULL,
language VARCHAR(255) NULL,
duration_minutes INT UNSIGNED NULL,
duration_text VARCHAR(255) NULL,
age_recommendation VARCHAR(255) NULL,
premiere_date DATE NULL,
cast_json JSON NULL,
team_json JSON NULL,
poster_storage ENUM('file', 'base64') NULL,
poster_path VARCHAR(1024) NULL,
poster_base64 LONGTEXT NULL,
poster_mime_type VARCHAR(100) NULL,
poster_source_url VARCHAR(2048) NULL,
poster_hash CHAR(64) NULL,
source_url VARCHAR(2048) NOT NULL,
last_seen_at TIMESTAMP NULL,
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
ON UPDATE CURRENT_TIMESTAMP,
INDEX idx_shows_title (title),
INDEX idx_shows_author (author),
INDEX idx_shows_director (director),
INDEX idx_shows_premiere_date (premiere_date)
)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS performances (
id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
show_id BIGINT UNSIGNED NOT NULL,
start_at TIMESTAMP NOT NULL,
end_at TIMESTAMP NULL,
venue VARCHAR(255) NULL,
performance_type VARCHAR(100) NULL,
status VARCHAR(50) NULL,
notes TEXT NULL,
source_url VARCHAR(2048) NULL,
last_seen_at TIMESTAMP NULL,
created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
ON UPDATE CURRENT_TIMESTAMP,
CONSTRAINT fk_performances_show
FOREIGN KEY (show_id)
REFERENCES shows(id)
ON DELETE CASCADE
ON UPDATE CASCADE,
INDEX idx_performances_show_id (show_id),
INDEX idx_performances_start_at (start_at),
INDEX idx_performances_venue (venue),
INDEX idx_performances_show_date (show_id, start_at)
)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci; 
USE theater_crawler;

ALTER TABLE shows 
ADD CONSTRAINT uq_shows_source_url UNIQUE (source_url(500));

ALTER TABLE performances 
ADD CONSTRAINT uq_performance_show_time UNIQUE (show_id, start_at);

#verificari
#toate idurile:
SELECT id, title, author, director, duration_text, age_recommendation, source_url 
FROM shows ;

#trb sa fie 37
SELECT COUNT(*) FROM shows;

#fiecare reprezentatie cu link ul ei
SELECT p.id, s.title, p.start_at, p.source_url 
FROM performances p 
JOIN shows s ON p.show_id = s.id;