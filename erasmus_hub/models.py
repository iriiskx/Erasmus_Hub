
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from uuid import uuid4


class User:
    
    @staticmethod
    def get_by_email(email):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    @staticmethod
    def create(email, password, role, name, faculty=None):
        import sqlite3
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (email, password, role, name, faculty)
                VALUES (?, ?, ?, ?, ?)
            """, (email, generate_password_hash(password), role, name, faculty))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    @staticmethod
    def verify_password(user, password):
        stored_password = user.get("password", "")
        if stored_password.startswith("pbkdf2:"):
            return check_password_hash(stored_password, password)
        return stored_password == password
    
    @staticmethod
    def get_all_students():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE role = 'student'")
        students = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return students
    
    @staticmethod
    def get_all():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    
    @staticmethod
    def update(email, name=None, faculty=None):
        conn = get_db()
        cursor = conn.cursor()
        updates = []
        params = []
        if name:
            updates.append("name = ?")
            params.append(name)
        if faculty is not None:
            updates.append("faculty = ?")
            params.append(faculty)
        if updates:
            params.append(email)
            cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE email = ?", params)
            conn.commit()
        conn.close()
    
    @staticmethod
    def update_password(email, new_password):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE email = ?", 
                      (generate_password_hash(new_password), email))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(email):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email = ?", (email,))
        conn.commit()
        conn.close()


class Application:
    
    @staticmethod
    def create(student_email, student_name, university, mobility_type, documents):
        from database import get_db
        import sqlite3
        
        conn = get_db()
        cursor = conn.cursor()
        app_id = str(uuid4())
        progress = int((len(documents) / 7) * 100) if documents else 0
        
        try:
            cursor.execute("""
                INSERT INTO applications (
                    id, student_email, student_name, university, mobility_type,
                    status, progress, submitted_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                app_id, student_email, student_name, university, mobility_type,
                "Podaná", progress, datetime.now().strftime("%d.%m.%Y"), datetime.now()
            ))
            
            for doc in documents:
                cursor.execute("""
                    INSERT INTO documents (
                        application_id, document_key, document_label, filename, status
                    ) VALUES (?, ?, ?, ?, ?)
                """, (app_id, doc["key"], doc["label"], doc["filename"], "Odoslaný"))
            
            conn.commit()
            return app_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_by_id(app_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        app = cursor.fetchone()
        conn.close()
        return dict(app) if app else None
    
    @staticmethod
    def get_by_student(student_email):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE student_email = ? ORDER BY created_at DESC", (student_email,))
        apps = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return apps
    
    @staticmethod
    def get_all():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications ORDER BY created_at DESC")
        apps = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return apps
    
    @staticmethod
    def get_by_status(status):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC", (status,))
        apps = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return apps
    
    @staticmethod
    def search(query):
        conn = get_db()
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute("""
            SELECT * FROM applications 
            WHERE university LIKE ? OR student_name LIKE ?
            ORDER BY created_at DESC
        """, (search_term, search_term))
        apps = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return apps
    
    @staticmethod
    def approve(app_id, admin_email):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE applications
            SET status = 'Schválená',
                approved_at = ?,
                approved_by = ?
            WHERE id = ?
        """, (datetime.now().strftime("%d.%m.%Y %H:%M"), admin_email, app_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def reject(app_id, admin_email, reason):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE applications
            SET status = 'Zamietnutá',
                rejected_at = ?,
                rejected_by = ?,
                rejection_reason = ?
            WHERE id = ?
        """, (datetime.now().strftime("%d.%m.%Y %H:%M"), admin_email, reason, app_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(app_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        conn.commit()
        conn.close()


class Document:
    
    @staticmethod
    def get_by_application(application_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE application_id = ?", (application_id,))
        docs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return docs
    
    @staticmethod
    def update_status(doc_id, status):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE documents SET status = ? WHERE id = ?", (status, doc_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_id(doc_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        doc = cursor.fetchone()
        conn.close()
        return dict(doc) if doc else None
    
    @staticmethod
    def add_to_application(application_id, document_key, document_label, filename):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO documents (application_id, document_key, document_label, filename, status)
            VALUES (?, ?, ?, ?, ?)
        """, (application_id, document_key, document_label, filename, "Odoslaný"))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(doc_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()


class Comment:
    
    @staticmethod
    def create(application_id, author_email, author_name, comment_text):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO application_comments (application_id, author_email, author_name, comment_text)
            VALUES (?, ?, ?, ?)
        """, (application_id, author_email, author_name, comment_text))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_application(application_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM application_comments
            WHERE application_id = ?
            ORDER BY created_at DESC
        """, (application_id,))
        comments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return comments


class Message:

    
    @staticmethod
    def create(from_email, from_name, from_role, to_email, to_role, message_text):

        conn = get_db()
        cursor = conn.cursor()
        msg_id = str(uuid4())
        cursor.execute("""
            INSERT INTO messages (id, from_email, from_name, from_role, to_email, to_role, message_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (msg_id, from_email, from_name, from_role, to_email, to_role, message_text))
        conn.commit()
        conn.close()
        return msg_id
    
    @staticmethod
    def get_by_user(user_email, user_role):

        conn = get_db()
        cursor = conn.cursor()
        if user_role == "student":
            cursor.execute("""
                SELECT * FROM messages
                WHERE from_email = ? OR to_email = ?
                ORDER BY created_at DESC
            """, (user_email, user_email))
        else:
            cursor.execute("""
                SELECT * FROM messages
                WHERE from_role = 'admin' OR to_role = 'admin'
                ORDER BY created_at DESC
            """)
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return messages
    
    @staticmethod
    def mark_read(msg_id, user_email=None):
        conn = get_db()
        cursor = conn.cursor()
        if user_email:
            cursor.execute("UPDATE messages SET is_read = 1 WHERE id = ? AND to_email = ?", (msg_id, user_email))
        else:
            cursor.execute("UPDATE messages SET is_read = 1 WHERE id = ?", (msg_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_unread_count(user_email, user_role):
        conn = get_db()
        cursor = conn.cursor()
        if user_role == "student":
            cursor.execute("""
                SELECT COUNT(*) FROM messages
                WHERE to_email = ? AND is_read = 0
            """, (user_email,))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM messages
                WHERE from_role = 'student' AND to_role = 'admin' AND is_read = 0
            """)
        count = cursor.fetchone()[0]
        conn.close()
        return count


class Announcement:
    
    @staticmethod
    def create(title, content, priority, author_email, author_name):
        conn = get_db()
        cursor = conn.cursor()
        ann_id = str(uuid4())
        cursor.execute("""
            INSERT INTO announcements (id, title, content, priority, author_email, author_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ann_id, title, content, priority, author_email, author_name))
        conn.commit()
        conn.close()
        return ann_id
    
    @staticmethod
    def get_all():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM announcements ORDER BY created_at DESC")
        announcements = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return announcements
    
    @staticmethod
    def get_by_id(ann_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM announcements WHERE id = ?", (ann_id,))
        ann = cursor.fetchone()
        conn.close()
        return dict(ann) if ann else None
    
    @staticmethod
    def update(ann_id, title, content, priority):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE announcements
            SET title = ?, content = ?, priority = ?, updated_at = ?
            WHERE id = ?
        """, (title, content, priority, datetime.now(), ann_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(ann_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM announcements WHERE id = ?", (ann_id,))
        conn.commit()
        conn.close()

