-- Library & Archives Mobile App + Admin Web Portal
-- Database Schema (MySQL) - 25CS1302E

CREATE DATABASE IF NOT EXISTS library_db;
USE library_db;

DROP TABLE IF EXISTS fines;
DROP TABLE IF EXISTS reservations;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS members;

CREATE TABLE members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(150) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    category VARCHAR(50),
    total_copies INT NOT NULL DEFAULT 1,
    available_copies INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_title (title),
    INDEX idx_author (author)
) ENGINE=InnoDB;

CREATE TABLE reservations (
    reservation_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    book_id INT NOT NULL,
    reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date DATE NOT NULL,
    returned_at TIMESTAMP NULL,
    status ENUM('ACTIVE','RETURNED','OVERDUE') DEFAULT 'ACTIVE',
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    INDEX idx_member_book (member_id, book_id)
) ENGINE=InnoDB;

CREATE TABLE fines (
    fine_id INT AUTO_INCREMENT PRIMARY KEY,
    reservation_id INT NOT NULL,
    amount DECIMAL(8,2) NOT NULL,
    paid BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Sample data so the demo has something to show
INSERT INTO members (name, email, phone) VALUES
('Prakshitha Malla', 'prakshitha@klh.edu.in', '9000000001'),
('Datla Sri Sai Purna Mahija', 'mahija@klh.edu.in', '9000000002');

INSERT INTO books (title, author, isbn, category, total_copies, available_copies) VALUES
('Database System Concepts', 'Silberschatz, Korth', '9780078022159', 'CS', 4, 3),
('Clean Code', 'Robert C. Martin', '9780132350884', 'CS', 3, 2),
('Distributed Systems', 'Tanenbaum', '9781530281756', 'CS', 2, 2);

INSERT INTO reservations (member_id, book_id, due_date, status) VALUES
(1, 1, '2026-09-20', 'ACTIVE');

INSERT INTO fines (reservation_id, amount, paid) VALUES
(1, 0.00, FALSE);

-- Login accounts (admin + member). Passwords are hashed by the backend on first
-- startup, not stored here in plain text — see main.py's startup routine.
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin','member') NOT NULL DEFAULT 'member',
    member_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE SET NULL
) ENGINE=InnoDB;
