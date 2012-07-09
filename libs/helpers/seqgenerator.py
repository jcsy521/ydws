# -*- coding: utf-8 -*-

import urllib2
from time import strftime, time
import random


class SeqGenerator(object):
    """Ask Seq Server for a uniq sequence number.
    """

    @staticmethod
    def next(db=None):
        """
        @param db: database handler.

        Format: yymmddHHMMSSXXXXXX
        
        the last 6 digits are generated from the primary key (auto_increment) of T_SEQ.
        """
        try:
            rowid = db.execute("INSERT INTO T_SEQ VALUES()")
            # NOTE: this is really tricky. 4294967295 is the max value of MySQL
            #       INT (unsigned). truncate the table in 1,000,000 to reset
            #       the auto increment column.
            if rowid == 1000000:
                db.execute("TRUNCATE T_SEQ")
        except:
            return str(random.randint(0, 9999))
        else:
            return ('%04d' % rowid)[-4:]
