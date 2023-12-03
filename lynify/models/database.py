import os
from typing import Optional

import psycopg2

from lynify.config import DATABASE_NAME, DATABASE_URL, POSTGRES_HOST, POSTGRES_PASSWORD, POSTGRES_PORT, POSTGRES_USER
from lynify.utils.utils import singleton


@singleton
class Database:
    """
    A class used to interface to a postgres database"""

    def __init__(self, database_name: Optional[str] = None, database_url: Optional[str] = None) -> None:
        if database_name is None:
            database_name = DATABASE_NAME
        if database_url is None:
            database_url = DATABASE_URL
        self.database_name = DATABASE_NAME
        self.database_url = DATABASE_URL
        if os.environ.get("APP_LOCATION") != "heroku":
            # conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            conn = psycopg2.connect(
                database="lynify",
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
            )
            conn.autocommit = True
            # check if the database exists
            c = conn.cursor()
            c.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = '" + self.database_name + "'")
            if c.fetchone() is None:
                c.execute("CREATE DATABASE " + self.database_name)
            conn.close()

    def connect(self):
        if os.environ.get("APP_LOCATION") == "heroku":
            return psycopg2.connect(DATABASE_URL, sslmode="require")
        return psycopg2.connect(
            database=self.database_name,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
        )

    def table_exists(self, table_name: str):
        conn = self.connect()
        c = conn.cursor()
        c.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '" + table_name + "')")
        if c.fetchone()[0] == 1:
            conn.close()
            return True
        else:
            conn.close()
            return False

    def drop_table(self, table_name: str):
        conn = self.connect()
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS " + table_name)
        conn.commit()
        conn.close()

    def create_table(self, table_name: str, columns: list):
        conn = self.connect()
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS " + table_name + " (" + ", ".join(columns) + ")")
        conn.commit()
        conn.close()

    def add_entry(self, table_name: str, columns: dict, values: list):
        column_names = [col.split()[0] for col in columns]
        sql = (
            "INSERT INTO "
            + table_name
            + " ("
            + ", ".join(column_names)
            + ") VALUES ("
            + ", ".join(["%s" for _ in column_names])
            + ")"
        )
        conn = self.connect()
        c = conn.cursor()
        c.execute(sql, values)
        conn.commit()
        conn.close()

    def get_entry(self, table_name: str, columns: list, values: list):
        column_names = [col.split()[0] for col in columns]
        conn = self.connect()
        c = conn.cursor()
        sql = "SELECT * FROM " + table_name + " WHERE " + " AND ".join([col + " = " + "%s" for col in column_names])
        c.execute(sql, values)
        result = c.fetchall()
        conn.close()
        return result

    def update_entry(self, table_name: str, columns: list, values: list, where_columns: list, where_values: list):
        column_names = [col.split()[0] for col in columns]
        where_column_names = [col.split()[0] for col in where_columns]
        conn = self.connect()
        c = conn.cursor()
        sql = (
            "UPDATE "
            + table_name
            + " SET "
            + ", ".join([col + " = " + "%s" for col in column_names])
            + " WHERE "
            + " AND ".join([col + " = " + "%s" for col in where_column_names])
        )
        c.execute(sql, values + where_values)
        conn.commit()
        conn.close()

    def get_all(self, table_name: str, order_by: Optional[str] = None):
        conn = self.connect()
        c = conn.cursor()
        if order_by is not None:
            c.execute("SELECT * FROM " + table_name + " ORDER BY " + order_by + " DESC")
        else:
            c.execute("SELECT * FROM " + table_name)
        result = c.fetchall()
        conn.close()
        return result

    def get_all_limit(self, table_name: str, limit: int, order_by: Optional[str] = None):
        conn = self.connect()
        c = conn.cursor()
        if order_by is not None:
            c.execute("SELECT * FROM " + table_name + " ORDER BY " + order_by + " DESC LIMIT " + str(limit))
        else:
            c.execute("SELECT * FROM " + table_name + " LIMIT " + str(limit))
        result = c.fetchall()
        conn.close()
        return result

    def get_all_limit_offset(self, table_name: str, limit: int, offset: int, order_by: Optional[str] = None):
        conn = self.connect()
        c = conn.cursor()
        if order_by is not None:
            c.execute(
                "SELECT * FROM "
                + table_name
                + " ORDER BY "
                + order_by
                + " DESC LIMIT "
                + str(limit)
                + " OFFSET "
                + str(offset)
            )
        else:
            c.execute("SELECT * FROM " + table_name + " LIMIT " + str(limit) + " OFFSET " + str(offset))
        result = c.fetchall()
        conn.close()
        return result

    def get_most_recent(self, table_name: str):
        conn = self.connect()
        c = conn.cursor()
        # check if the table has a timestamp column
        c.execute(
            "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = '"
            + table_name
            + "' AND column_name = 'timestamp')"
        )
        if c.fetchone()[0] == 0:
            # return the last added
            c.execute("SELECT * FROM " + table_name + " ORDER BY ROWID DESC LIMIT 1")
        c.execute("SELECT * FROM " + table_name + " ORDER BY timestamp DESC LIMIT 1")
        result = c.fetchall()
        conn.close()
        return result

    def get_with_left_join(
        self,
        table_name: str,
        join_table_name: str,
        join_column: str,
        join_table_column: str,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ):
        conn = self.connect()
        c = conn.cursor()
        if order_by is not None:
            if limit is not None and offset is not None:
                c.execute(
                    "SELECT * FROM "
                    + table_name
                    + " LEFT JOIN "
                    + join_table_name
                    + " ON "
                    + table_name
                    + "."
                    + join_column
                    + " = "
                    + join_table_name
                    + "."
                    + join_table_column
                    + " ORDER BY "
                    + order_by
                    + " DESC LIMIT "
                    + str(limit)
                    + " OFFSET "
                    + str(offset)
                )
            else:
                c.execute(
                    "SELECT * FROM "
                    + table_name
                    + " LEFT JOIN "
                    + join_table_name
                    + " ON "
                    + table_name
                    + "."
                    + join_column
                    + " = "
                    + join_table_name
                    + "."
                    + join_table_column
                    + " ORDER BY "
                    + order_by
                    + " DESC"
                )
        else:
            if limit is not None and offset is not None:
                c.execute(
                    "SELECT * FROM "
                    + table_name
                    + " LEFT JOIN "
                    + join_table_name
                    + " ON "
                    + table_name
                    + "."
                    + join_column
                    + " = "
                    + join_table_name
                    + "."
                    + join_table_column
                    + " LIMIT "
                    + str(limit)
                    + " OFFSET "
                    + str(offset)
                )
            else:
                c.execute(
                    "SELECT * FROM "
                    + table_name
                    + " LEFT JOIN "
                    + join_table_name
                    + " ON "
                    + table_name
                    + "."
                    + join_column
                    + " = "
                    + join_table_name
                    + "."
                    + join_table_column
                )
        result = c.fetchall()
        conn.close()
        return result
