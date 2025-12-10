import sqlite3
import os
from datetime import datetime

DATABASE = "erasmus_hub.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'admin')),
            name TEXT NOT NULL,
            faculty TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            student_email TEXT NOT NULL,
            student_name TEXT NOT NULL,
            university TEXT NOT NULL,
            mobility_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Podaná' CHECK(status IN ('Podaná', 'Schválená', 'Zamietnutá')),
            progress INTEGER DEFAULT 0,
            submitted_date TEXT,
            approved_at TEXT,
            approved_by TEXT,
            rejected_at TEXT,
            rejected_by TEXT,
            rejection_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_email) REFERENCES users(email)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL,
            document_key TEXT NOT NULL,
            document_label TEXT NOT NULL,
            filename TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Odoslaný' CHECK(status IN ('Odoslaný', 'V preverovaní', 'Schválený', 'Zamietnutý')),
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS application_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL,
            author_email TEXT NOT NULL,
            author_name TEXT NOT NULL,
            comment_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
            FOREIGN KEY (author_email) REFERENCES users(email)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            from_email TEXT NOT NULL,
            from_name TEXT NOT NULL,
            from_role TEXT NOT NULL,
            to_email TEXT,
            to_role TEXT NOT NULL,
            message_text TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_email) REFERENCES users(email)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'normal' CHECK(priority IN ('low', 'normal', 'high')),
            author_email TEXT NOT NULL,
            author_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (author_email) REFERENCES users(email)
        )
    """)
    
    conn.commit()
    conn.close()
    
    create_default_users()


def create_default_users():
    from werkzeug.security import generate_password_hash
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.execute("""
            INSERT INTO users (email, password, role, name)
            VALUES (?, ?, ?, ?)
        """, (
            "student@example.com",
            generate_password_hash("student"),
            "student",
            "Ján Študent"
        ))
        
        cursor.execute("""
            INSERT INTO users (email, password, role, name)
            VALUES (?, ?, ?, ?)
        """, (
            "admin@example.com",
            generate_password_hash("admin"),
            "admin",
            "Mária Nováková"
        ))
        
        conn.commit()
    
    conn.close()


def migrate_from_json():
    import json
    from werkzeug.security import generate_password_hash
    from uuid import uuid4
    
    conn = get_db()
    cursor = conn.cursor()
    if os.path.exists("users.json"):
        try:
            with open("users.json", "r", encoding="utf-8") as f:
                users_data = json.load(f)
                for email, user_data in users_data.items():
                    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                    if not cursor.fetchone():
                        password = user_data.get("password", "")
                        if not password.startswith("pbkdf2:"):
                            password = generate_password_hash(password)
                        
                        cursor.execute("""
                            INSERT INTO users (email, password, role, name, faculty)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            email,
                            password,
                            user_data.get("role", "student"),
                            user_data.get("name", ""),
                            user_data.get("faculty", "")
                        ))
        except Exception as e:
            print(f"Помилка міграції користувачів: {e}")
    
    if os.path.exists("applications.json"):
        try:
            with open("applications.json", "r", encoding="utf-8") as f:
                apps_data = json.load(f)
                for app in apps_data:
                    app_id = app.get("id", str(uuid4()))
                    cursor.execute("SELECT id FROM applications WHERE id = ?", (app_id,))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO applications (
                                id, student_email, student_name, university, mobility_type,
                                status, progress, submitted_date, approved_at, approved_by,
                                rejected_at, rejected_by, rejection_reason, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            app_id,
                            app.get("student_email", ""),
                            app.get("student_name", ""),
                            app.get("university", ""),
                            app.get("type", "Štúdium"),
                            app.get("status", "Podaná"),
                            app.get("progress", 0),
                            app.get("submitted", ""),
                            app.get("approved_at"),
                            app.get("approved_by"),
                            app.get("rejected_at"),
                            app.get("rejected_by"),
                            app.get("rejection_reason"),
                            app.get("created_at", datetime.now().isoformat())
                        ))
                        
                        for doc in app.get("documents", []):
                            cursor.execute("""
                                INSERT INTO documents (
                                    application_id, document_key, document_label, filename, status
                                ) VALUES (?, ?, ?, ?, ?)
                            """, (
                                app_id,
                                doc.get("key", ""),
                                doc.get("label", ""),
                                doc.get("filename", ""),
                                doc.get("status", "Odoslaný")
                            ))
                        
                        for comment in app.get("comments", []):
                            cursor.execute("""
                                INSERT INTO application_comments (
                                    application_id, author_email, author_name, comment_text, created_at
                                ) VALUES (?, ?, ?, ?, ?)
                            """, (
                                app_id,
                                comment.get("author_email", ""),
                                comment.get("author", ""),
                                comment.get("text", ""),
                                comment.get("created_at", datetime.now().strftime("%d.%m.%Y %H:%M"))
                            ))
        except Exception as e:
            print(f"Помилка міграції заявок: {e}")
    
    if os.path.exists("messages.json"):
        try:
            with open("messages.json", "r", encoding="utf-8") as f:
                messages_data = json.load(f)
                for msg in messages_data:
                    msg_id = msg.get("id", str(uuid4()))
                    cursor.execute("SELECT id FROM messages WHERE id = ?", (msg_id,))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO messages (
                                id, from_email, from_name, from_role, to_email, to_role,
                                message_text, is_read, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            msg_id,
                            msg.get("from_email", ""),
                            msg.get("from_name", ""),
                            msg.get("from_role", ""),
                            msg.get("to_email"),
                            msg.get("to_role", ""),
                            msg.get("text", ""),
                            1 if msg.get("read", False) else 0,
                            msg.get("created_at", datetime.now().strftime("%d.%m.%Y %H:%M"))
                        ))
        except Exception as e:
            print(f"Помилка міграції повідомлень: {e}")
    
    if os.path.exists("announcements.json"):
        try:
            with open("announcements.json", "r", encoding="utf-8") as f:
                anns_data = json.load(f)
                for ann in anns_data:
                    ann_id = ann.get("id", str(uuid4()))
                    cursor.execute("SELECT id FROM announcements WHERE id = ?", (ann_id,))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO announcements (
                                id, title, content, priority, author_email, author_name, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            ann_id,
                            ann.get("title", ""),
                            ann.get("content", ""),
                            ann.get("priority", "normal"),
                            ann.get("created_by", ""),
                            ann.get("author_name", ""),
                            ann.get("created_at", datetime.now().strftime("%d.%m.%Y %H:%M"))
                        ))
        except Exception as e:
            print(f"Помилка міграції новин: {e}")
    
    conn.commit()
    conn.close()



