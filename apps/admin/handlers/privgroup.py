# -*- coding: utf-8 -*-

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS
from utils.checker import check_sql_injection

from base import BaseHandler, authenticated

from constants import PRIVILEGES
from checker import check_privileges


class PrivGroupListHandler(BaseHandler):

    @authenticated
    @check_privileges([PRIVILEGES.MANAGE_PRIVILEGE_GROUP])
    @tornado.web.removeslash
    def get(self):
        """
        list all privilege groups.
        """

        priv_groups = {}

        # TODO: create views
        user_count = self.db.query("SELECT tpg.id, count(tp.administrator_id) AS count"
                                   "  FROM T_PRIVILEGE_GROUP AS tpg"
                                   "  LEFT JOIN T_PRIVILEGE AS tp"
                                   "    ON tp.privilege_group_id = tpg.id"
                                   "  GROUP BY tpg.id")
        if user_count:
            rs = self.db.query("SELECT tpg.id, tpg.name, tpg.builtin,"
                               "       tpgd.privilege_id, tmp.name AS privilege_name"
                               "  FROM T_PRIVILEGE_GROUP AS tpg"
                               "  LEFT JOIN (T_PRIVILEGE_GROUP_DATA AS tpgd,"
                               "             T_META_PRIVILEGE AS tmp)"
                               "    ON (tpg.id = tpgd.privilege_group_id"
                               "        AND tpgd.privilege_id = tmp.id)")
            for r in rs:
                if not r.id in priv_groups:
                    priv_groups[r.id] = DotDict(name=r.name,
                                                builtin=r.builtin,
                                                num=[u.count for u in user_count if u.id == r.id][0],
                                                privileges=[])
                if r.privilege_id is not None:
                    priv_groups[r.id].privileges.append((r.privilege_id, r.privilege_name))
        for i, key in enumerate(priv_groups.keys()):
            priv_groups[key].seq = i + 1
            
        self.render("privgroup/list.html",
                    groups=priv_groups)


class PrivGroupMixin:

    def get_priv_group_info(self, priv_group_id):

        rs = self.db.query("SELECT tpg.name, tpg.builtin, tpgd.privilege_id"
                           "  FROM T_PRIVILEGE_GROUP AS tpg"
                           "  LEFT JOIN T_PRIVILEGE_GROUP_DATA AS tpgd"
                           "    ON tpg.id = tpgd.privilege_group_id"
                           "  WHERE tpg.id = %s",
                           priv_group_id)
        info = None
        if rs:
            info = DotDict(id=priv_group_id,
                           name=rs[0].name,
                           builtin=rs[0].builtin,
                           privileges=[r.privilege_id for r in rs if r.privilege_id])
        return info

        
class PrivGroupEditHandler(BaseHandler, PrivGroupMixin):

    @authenticated
    @check_privileges([PRIVILEGES.MANAGE_PRIVILEGE_GROUP])
    @tornado.web.removeslash
    def get(self, priv_group_id):

        success = True
        message = None

        priv_group = self.get_priv_group_info(priv_group_id)
        privileges = None
        if not priv_group:
            success = False
            message = ErrorCode.PRIV_GROUP_NOT_FOUND
        elif priv_group.builtin:
            success = False
            message = ErrorCode.EDIT_META_PRIVILEGE
        else:
            # todo: this should be revised.
            privileges = self.db.query("SELECT * FROM T_META_PRIVILEGE")

        self.render("privgroup/edit.html",
                    group=priv_group,
                    privileges=privileges,
                    success=success,
                    message=message)
        
    @authenticated
    @check_privileges([PRIVILEGES.MANAGE_PRIVILEGE_GROUP])
    @tornado.web.removeslash
    def post(self, priv_group_id):

        privileges = self.get_arguments('privilege')
        if privileges:
            self.db.execute("DELETE FROM T_PRIVILEGE_GROUP_DATA"
                            "  WHERE privilege_group_id = %s",
                            priv_group_id)
            self.db.executemany("INSERT INTO T_PRIVILEGE_GROUP_DATA"
                                "  VALUES (%s, %s)",
                                [(priv_group_id, priv) for priv in privileges])
        
        self.redirect("/privgroup/list")

        
class PrivGroupCreateHandler(BaseHandler):

    @authenticated
    @check_privileges([PRIVILEGES.MANAGE_PRIVILEGE_GROUP])
    @tornado.web.removeslash
    def get(self):

        privileges = self.db.query("SELECT * FROM T_META_PRIVILEGE")
        self.render("privgroup/create.html",
                    privileges=privileges)

    @authenticated
    @check_privileges([PRIVILEGES.MANAGE_PRIVILEGE_GROUP])
    @tornado.web.removeslash
    def post(self):

        name = self.get_argument('name', '')
        #if not check_sql_injection(name):
        #    self.get()
        #    return
        privileges = self.get_arguments('privilege')
        priv_group_id = self.db.execute("INSERT INTO T_PRIVILEGE_GROUP"
                                        "  VALUES (NULL, %s, 0)",
                                        name)
        
        self.db.executemany("INSERT INTO T_PRIVILEGE_GROUP_DATA"
                            "  VALUES (%s, %s)",
                            [(priv_group_id, priv) for priv in privileges])
        
        self.redirect("/privgroup/list")


class PrivGroupDeleteHandler(BaseHandler):

    @authenticated
    @check_privileges([PRIVILEGES.MANAGE_PRIVILEGE_GROUP])
    @tornado.web.removeslash
    def post(self, priv_group_id):

        self.db.execute("DELETE FROM T_PRIVILEGE_GROUP"
                        "  WHERE id = %s"
                        "    AND builtin = 0",
                        priv_group_id)

        ret = dict(success=0)
        self.set_header(*self.JSON_HEADER)
        self.write(json_encode(ret))
