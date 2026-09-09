-- Library Book Manager Database Schema

DROP TABLE IF EXISTS issue_records;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS members;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin'
);

CREATE TABLE books (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    publisher TEXT,
    isbn TEXT,
    category TEXT,
    total_copies INTEGER NOT NULL DEFAULT 1,
    available_copies INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE members (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    join_date TEXT NOT NULL
);

CREATE TABLE issue_records (
    issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    return_date TEXT,
    fine_amount REAL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Issued',
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (member_id) REFERENCES members(member_id)
);

-- Default admin login: username = admin, password = admin123
INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin');

-- Sample books
INSERT INTO books (title, author, publisher, isbn, category, total_copies, available_copies) VALUES
('The Pragmatic Programmer', 'Andrew Hunt', 'Addison-Wesley', '9780135957059', 'Computer Science', 3, 3),
('Introduction to Algorithms', 'Cormen, Leiserson, Rivest', 'MIT Press', '9780262033848', 'Computer Science', 2, 2),
('Database System Concepts', 'Silberschatz', 'McGraw-Hill', '9780078022159', 'Computer Science', 4, 4),
('Wings of Fire', 'A.P.J. Abdul Kalam', 'Universities Press', '9788173711466', 'Biography', 2, 2),
('The Alchemist', 'Paulo Coelho', 'HarperCollins', '9780062315007', 'Fiction', 3, 3),
('Clean Code', 'Robert C. Martin', 'Prentice Hall', '9780132350884', 'Computer Science', 2, 2),
('Sapiens', 'Yuval Noah Harari', 'Harper', '9780062316097', 'History', 2, 2),
('Operating System Concepts', 'Silberschatz, Galvin', 'Wiley', '9781118063330', 'Computer Science', 3, 3),
('Rich Dad Poor Dad', 'Robert Kiyosaki', 'Plata Publishing', '9781612680194', 'Finance', 2, 2),
('A Brief History of Time', 'Stephen Hawking', 'Bantam', '9780553380163', 'Science', 2, 2);

-- Sample members
INSERT INTO members (name, email, phone, address, join_date) VALUES
('Rahul Sharma', 'rahul.sharma@example.com', '9876543210', 'Delhi', date('now', '-150 days')),
('Priya Verma', 'priya.verma@example.com', '9876543211', 'Noida', date('now', '-120 days')),
('Amit Kumar', 'amit.kumar@example.com', '9876543212', 'Gurugram', date('now', '-90 days')),
('Sneha Gupta', 'sneha.gupta@example.com', '9876543213', 'Delhi', date('now', '-60 days'));

-- Sample issue records spread across the last several months so the
-- dashboard charts have something meaningful to show.
INSERT INTO issue_records (book_id, member_id, issue_date, due_date, return_date, fine_amount, status) VALUES
-- currently issued (one overdue, one active)
(1, 1, date('now', '-20 days'), date('now', '-6 days'), NULL, 0, 'Issued'),
(3, 2, date('now', '-5 days'), date('now', '+9 days'), NULL, 0, 'Issued'),

-- returned, spread across recent months for the "issued per month" chart
(5, 3, date('now', '-150 days'), date('now', '-136 days'), date('now', '-140 days'), 0, 'Returned'),
(6, 1, date('now', '-145 days'), date('now', '-131 days'), date('now', '-135 days'), 0, 'Returned'),
(2, 2, date('now', '-120 days'), date('now', '-106 days'), date('now', '-110 days'), 0, 'Returned'),
(7, 4, date('now', '-115 days'), date('now', '-101 days'), date('now', '-105 days'), 0, 'Returned'),
(1, 3, date('now', '-90 days'), date('now', '-76 days'), date('now', '-80 days'), 0, 'Returned'),
(8, 2, date('now', '-88 days'), date('now', '-74 days'), date('now', '-70 days'), 20, 'Returned'),
(6, 4, date('now', '-60 days'), date('now', '-46 days'), date('now', '-50 days'), 0, 'Returned'),
(3, 1, date('now', '-58 days'), date('now', '-44 days'), date('now', '-40 days'), 0, 'Returned'),
(9, 3, date('now', '-55 days'), date('now', '-41 days'), date('now', '-45 days'), 0, 'Returned'),
(2, 4, date('now', '-30 days'), date('now', '-16 days'), date('now', '-20 days'), 0, 'Returned'),
(6, 2, date('now', '-28 days'), date('now', '-14 days'), date('now', '-18 days'), 0, 'Returned'),
(1, 4, date('now', '-25 days'), date('now', '-11 days'), date('now', '-12 days'), 0, 'Returned'),
(10, 1, date('now', '-15 days'), date('now', '-1 days'), date('now', '-3 days'), 0, 'Returned'),
(8, 3, date('now', '-12 days'), date('now', '+2 days'), date('now', '-2 days'), 0, 'Returned');

UPDATE books SET available_copies = available_copies - 1 WHERE book_id IN (1, 3);
