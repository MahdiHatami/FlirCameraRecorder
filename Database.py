import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS defects "
            "(id INTEGER PRIMARY KEY, "
            "created_date TEXT, "
            "defect_type TEXT,"
            "image_path TEXT,"
            "is_valid INTEGER)")
        self.conn.commit()

    def fetch(self, hostname=''):
        self.cur.execute(
            "SELECT id, datetime('created_date'), defect_type, image_path, is_valid;"
            " FROM defects WHERE hostname LIKE ?", ('%' + hostname + '%',))
        rows = self.cur.fetchall()
        return rows

    def fetch_all(self):
        self.cur.execute(
            "SELECT id, datetime('created_date'), defect_type, image_path, is_valid;"
            " FROM defects")
        rows = self.cur.fetchall()
        return rows

    def insert(self, created_date, defect_type, image_path, is_valid):
        self.cur.execute("INSERT INTO defects VALUES (NULL, ?, ?, ?, ?)",
                         (datetime(created_date), defect_type, image_path, is_valid))
        self.conn.commit()

    def remove(self, id):
        self.cur.execute("DELETE FROM defects WHERE id=?", (id,))
        self.conn.commit()

    def update(self, created_date, defect_type, image_path, is_valid):
        self.cur.execute(
            "UPDATE defects SET created_date = ?, defect_type = ?, image_path = ?, is_valid = ? WHERE id = ?",
            (created_date, defect_type, image_path, is_valid, id))
        self.conn.commit()

    def __del__(self):
        self.conn.close()
