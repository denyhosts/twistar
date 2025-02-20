from __future__ import absolute_import
import mysql.connector

from twisted.enterprise import adbapi
from twisted.python import log

from twistar.dbconfig.base import InteractionBase


class MysqlDBConfig(InteractionBase):
    includeBlankInInsert = False

    def insertArgsToString(self, vals):
        if len(vals) > 0:
            return "(" + ",".join(["%s" for _ in vals.items()]) + ")"
        return "VALUES ()"


class ReconnectingMySQLConnectionPool(adbapi.ConnectionPool):
    """
    This connection pool will reconnect if the server goes away.  This idea was taken from:
    http://www.gelens.org/2009/09/13/twisted-connectionpool-revisited/
    """
    def _runInteraction(self, interaction, *args, **kw):
        try:
            return adbapi.ConnectionPool._runInteraction(self, interaction, *args, **kw)
        except mysql.connector.OperationalError as e:
            if e[0] not in (2006, 2013):
                raise
            log.err("Lost connection to MySQL, retrying operation.  If no errors follow, retry was successful.")
            conn = self.connections.get(self.threadID())
            self.disconnect(conn)
            return adbapi.ConnectionPool._runInteraction(self, interaction, *args, **kw)
