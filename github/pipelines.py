import sqlite3
import os

con = None


class GithubPipeline(object):
    def __init__(self):
        self.setupDBCon()
        self.createTables()

    def setupDBCon(self):
        self.con = sqlite3.connect(os.getcwd() + "/emails.db")
        self.cur = self.con.cursor()

    def createTables(self):
        self.createTable()

    def closeDB(self):
        self.con.close()

    def __del__(self):
        self.closeDB()

    def createTable(self):
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS Github(id INTEGER PRIMARY KEY NOT NULL, email TEXT)"
        )

    def process_item(self, item, spider):
        if spider.name == "github_spider":
            self.storeInDb(item)
        return item

    def storeInDb(self, item):
        self.cur.execute(
            "SELECT COUNT(*) FROM Github where email=?", [item.get("email")]
        )

        (rows,) = self.cur.fetchone()

        if rows == 0:
            self.cur.execute("INSERT INTO Github(email) VALUES(?)", [item.get("email")])
            print("------------------------")
            print("Data Stored in Database")
            print("------------------------")
            self.con.commit()
