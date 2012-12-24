#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A lightweight wrapper around cx_Oracle."""

import cx_Oracle
import os
#solve Chinese encoding problem
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8' 
import itertools
import logging
import re


class Connection(object):
    """A lightweight wrapper around cx_Oracle DB-API connections.

    The main value we provide is wrapping rows in a dict/object so that
    columns can be accessed by name. Typical usage:

        db = oracledb.Connection("localhost:port", "database", "user", "password")
        for user in db.query("SELECT * FROM T_USER"):
            print user.name

    Cursors are hidden by the implementation, but other than that, the methods
    are very similar to the DB-API.
    """
    def __init__(self, host="192.168.1.3:1521", database_sid="DBACBNEW", user="scott", password="tiger"):
        pair = host.split(":")
        if len(pair) == 2:
            self.host = pair[0]
            self.port = pair[1]
            
        else:
            self.host = host
            self.port = 1521
            
        self.database = database_sid
        self.user = user
        self.password = password
        self._db = None
        try:
            self.connect()
        except:
            logging.error("Cannot connect to Oracle database : %s", self.database,
                          exc_info=True)

    def __del__(self):
        self.close()

    def close(self):
        """Closes this database connection."""
        if getattr(self, "_db", None) is not None:
            self._db.close()
            self._db = None

    def connect(self):
        """Closes the existing database connection and re-opens it."""
        self.close()
        tns = cx_Oracle.makedsn(self.host, self.port, self.database)
        self._db = cx_Oracle.connect(self.user, self.password, tns)
        self._db.autocommit = 1

    def query(self, query, *parameters):
        """Returns a row list for the given query and parameters."""
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters)
            column_names = [d[0] for d in cursor.description]
            return [Row(itertools.izip(column_names, row)) for row in cursor]
        except Exception as e:
            logging.exception("oracledb query() exception")
#            cursor.close()
#            # todo
#            self.close()
        finally:
            cursor.close()

    def get(self, query, *parameters):
        """Returns the first row returned for the given query."""
        rows = self.query(query, *parameters)
        if not rows:
            return None
        elif len(rows) > 1:
            raise Exception("Multiple rows returned for oracledb.get() query")
        else:
            return rows[0]

    def execute(self, query, *parameters):
        """Executes the given query, returning the lastrowid from the query."""
        cursor = self._cursor()
        try:
            print parameters
            self._execute(cursor, query, parameters)
            return cursor.rowcount
        except Exception as e:
            logging.exception("oracledb execute() exception")
#            cursor.close()
#            self.close()
        finally:
            cursor.close()

    def get_id(self, query):
        cursor = self._cursor()
        try:
            cursor.execute(query)
            return cursor.fetchone()[0]
        except Exception as e:
            logging.exception("oracledb get_id() exception")
            
    def executemany(self, query, parameters):
        """Executes the given query against all the given param sequences.

        We return the lastrowid from the query.
        """
        cursor = self._cursor()
        try:
            cursor.executemany(query, parameters)
            return cursor.rowcount
        finally:
            cursor.close()

    def _cursor(self):
        return self._db.cursor()

    def _execute(self, cursor, query_temple, parameters):
        try:
            query = get_query(query_temple, parameters)
            print query
            return cursor.execute(query)
        except Exception as e:
            logging.exception("oracledb _execute() exception")
            raise
        
def get_query(query_temple, parameters):
    # shield Oracle keywords, well tried ,the following method is ture !!!
    if re.search('ID|id', query_temple):
        query_temple = re.sub("ID|id", "\"ID\"", query_temple)
    if re.search("(u|U)\"ID\"", query_temple):
        query_temple = re.sub("(u|U)\"ID\"", "\"UID\"", query_temple)
        
    if re.search('%%%%%s%%%%', query_temple):
        query_temple = re.sub("%%%%%s%%%%", "'%%%%%s%%%%'", query_temple)
    else:
        query_temple = re.sub("%s", "'%s'", query_temple)
    return query_temple % parameters


class Row(dict):
    """A dict that allows for object-like property access syntax."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


if __name__ == "__main__":
    db = Connection()
    print db.query("select * from emp")
#    rs = db.get("select * from emp where empno = 7876")
#    print rs
#    print rs["ENAME"]
#    num = db.execute("insert into emp(EMPNO, ENAME, JOB, MGR, SAL, COMM, DEPTNO)"
#                     " values(%s, %s, %s, %s, %s, %s, %s)",
#                     8888, 'liu', 'analyst', 7698, 3000, 1000, 20)
#    
#    db.execute("update emp set SAL = %s where EMPNO = %s", 60000, 8888)
    
#    id = db.get_id("SELECT T_USER_SEQ.NEXTVAL FROM DUAL")
#    print id 
#    db.execute("insert into t_user(id, uid, password, name, mobile, address, email, remark) "
#               "  values(%s, %s, %s, %s, %s, %s, %s, %s)",
#               id, 15010958888, 111111, '刘时嘉', 15010958888, '硅谷亮城', 'xxx@gmail.com', 'xxx')
#    db.execute("delete from emp where EMPNO = %s", 8888)
#    num = db.execute("insert into emp(EMPNO, ENAME, JOB, MGR, SAL, COMM, DEPTNO)"
#                     " values('%s', '%s', '%s', '%s', '%s', '%s', '%s')",
#                     8888, "liu", "MANAGER", 7698, 2000, 500, 20)
#    num = db.execute("insert into emp(EMPNO, ENAME, JOB, MGR, SAL, COMM, DEPTNO)"
#                     " values(:EMPNO, :ENAME, :JOB, :MGR, :SAL, :COMM, :DEPTNO)",
#                     dict(EMPNO=8888, ENAME="刘", JOB="MANAGER", MGR=7698, SAL=2000, COMM=500, DEPTNO=20))
#    num = db.execute("insert into emp(EMPNO, ENAME, JOB, MGR, SAL, COMM, DEPTNO)"
#                     " values(:1, :2, :3, :4, :5, :6, :7)",
#                     8888, "刘", "MANAGER", 7698, 2000, 500, 20)
#    print num
    db.close()
