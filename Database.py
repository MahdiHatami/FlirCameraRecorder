import sqlite3


class Database:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.cur = self.conn.cursor()
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS defects "
            "(id INTEGER PRIMARY KEY, "
            "record_created_date timestamp, "
            "defect_created_date timestamp, "
            "defect_type TEXT,"
            "image_path TEXT,"
            "defect_location INTEGER,"
            "is_valid INTEGER)")
        self.conn.commit()

    def fetch(self, defect_type):
        self.cur.execute(
            "SELECT id, datetime('created_date'), defect_type, image_path, is_valid;"
            " FROM defects WHERE defect_type LIKE ?", ('%' + defect_type + '%',))
        rows = self.cur.fetchall()
        return rows

    def fetch_all(self):
        self.cur.execute("SELECT * FROM defects")
        rows = self.cur.fetchall()
        return rows

    def insert(self, record_create_date, created_date, defect_type, image_path, defect_location, is_valid):
        self.cur.execute("INSERT INTO defects VALUES (NULL, ?, ?, ?, ?, ?, ?)",
                         (record_create_date, created_date, defect_type, image_path, defect_location, is_valid))
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
