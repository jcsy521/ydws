# -*- coding: utf-8 -*-

"""
How to use these privilege checking decorators?

Sample
======
@tornado.web.authenticated
@tornado.web.removeslash
@check_privileges(privileges, error_page)
@check_areas(error_page)
def post(self):
    pass

You'd better put these decorators after tornado's decorators, because
they assume the use has been logged in.
"""

import functools

from constants import AREA
from utils.misc import DUMMY_IDS
from utils.misc import str_to_list

from errors import ErrorCode


def check_areas(error_page="errors/priv.html"):
    """
    Decorator used to check whether the current user is allowed to
    work on areas.

    area info will be get from self.request. 'province_id' and
    'city_id' are expected.
    """
    
    def _internal_check(administrator_id, city_ids, group_ids, db):

        admin = db.get("SELECT type FROM T_ADMINISTRATOR"
                       "  WHERE id = %s", administrator_id)
        if admin.type == 0:
            return True 
            
        if city_ids:
            rs = db.query("SELECT area_id"
                          "  FROM T_AREA_PRIVILEGE"
                          "  WHERE administrator_id = %s"
                          "    AND category = %s"
                          "    AND area_id in %s",
                          administrator_id, AREA.CATEGORY.CITY,
                          tuple(city_ids + DUMMY_IDS))
            # you may have the province permission, so recheck the province_id
            recheck_ids = set(city_ids) - set([r.area_id for r in rs])
            if recheck_ids:
                # check each city
                for city_id in recheck_ids:
                    r = db.get("SELECT DISTINCT thc.region_code"
                               "  FROM T_AREA_PRIVILEGE AS tap,"
                               "       T_HLR_CITY AS thc"
                               "  WHERE thc.city_id = %s"
                               "    AND thc.province_id = tap.area_id"
                               "    AND tap.category = %s"
                               "    AND tap.administrator_id = %s",
                               city_id, 
                               AREA.CATEGORY.PROVINCE,
                               administrator_id)
                    if not r:
                        return False
        elif province_ids:

            rs = db.query("SELECT area_id"
                          "  FROM T_AREA_PRIVILEGE"
                          "  WHERE administrator_id = %s"
                          "    AND category = %s"
                          "    AND area_id in %s",
                          administrator_id, AREA.CATEGORY.PROVINCE,
                          tuple(province_ids + DUMMY_IDS))
            not_permitted = set(province_ids) - set([r.area_id for r in rs])
            if not_permitted:
                return False
        else:
            # True or False?
            pass

        # group_ids is optional
        if group_ids:
            res = db.query("SELECT txg.xxt_id"
                           "  FROM T_XXT_GROUP AS txg, T_HLR_CITY AS thc, T_AREA_PRIVILEGE AS tap"
                           "  WHERE tap.administrator_id = %s"
                           "    AND txg.xxt_id in %s"
                           "    AND ((txg.city_id = tap.area_id AND tap.category = %s)"
                           "    OR (txg.city_id = thc.region_code AND thc.province_id = tap.area_id AND tap.category = %s))",
                           administrator_id, group_ids + DUMMY_IDS, AREA.CATEGORY.CITY, AREA.CATEGORY.PROVINCE)
            if not res:
                return False

        return True


    def decorator(method):

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            province_ids = map(int, str_to_list(self.get_argument('province_id', '')))
            city_ids = map(int, str_to_list(self.get_argument('city_id', '')))
            group_ids = map(int, str_to_list(self.get_argument('group', '')))

            is_permitted = _internal_check(self.current_user.id,
                                           province_ids,
                                           city_ids,
                                           group_ids,
                                           self.db)
            if is_permitted:
                return method(self, *args, **kwargs)
            else:
                self.render(error_page,
                            error=True,
                            message=ErrorCode.PERMISSION_DENIED)

        return wrapper
    return decorator


def check_privileges(privileges, error_page="errors/priv.html"):

    """
    Decorator used to check whether the current user is allowed to
    perform certain actions.

    @param privileges: a list of privileges' mnemonics. these
    privileges are required to enter the wrapped function.
    @param web_page: render the page if error occurs.
    """
    
    def _internal_check(administrator_id, privileges, db):
        
        rs = db.query("SELECT DISTINCT tpgd.privilege_id"
                      "  FROM T_PRIVILEGE AS tp,"
                      "       T_PRIVILEGE_GROUP_DATA AS tpgd"
                      "  WHERE tp.privilege_group_id = tpgd.privilege_group_id"
                      "    AND tp.administrator_id = %s",
                      administrator_id)
        permitted_privs = [int(r.privilege_id) for r in rs]
        if set(privileges) - set(permitted_privs):
            # there are unfullfilled privileges, deny the access
            return False
        return True

    def decorator(method):

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            is_permitted = _internal_check(self.current_user.id,
                                           privileges,
                                           self.db)
            if is_permitted:
                return method(self, *args, **kwargs)
            else:
                self.render(error_page,
                            error=True,
                            message=ErrorCode.PERMISSION_DENIED)

        return wrapper
    return decorator

