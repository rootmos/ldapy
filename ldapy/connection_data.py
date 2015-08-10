# This file is part of ldapy.
#
# ldapy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ldapy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ldapy.  If not, see <http://www.gnu.org/licenses/>.

import json

import logging
logger = logging.getLogger("ldapy.%s" % __name__)

class ConnectionData:
    """A simple container for connection data, eg URI and bind DN"""
    def __init__ (self, uri, bind_dn, password = None):
        self.uri = uri
        self.bind_dn = bind_dn
        self.password = password

    @staticmethod
    def load (data):
        try:
            return ConnectionData (data["uri"], data["bind_dn"], data["password"])
        except KeyError, key:
            raise SyntaxError("Syntax error parsing connection data: no %s field" % key)

class ConnectionDataManager:
    """A class for managing ConnectionData items for recent and saved
    connections"""

    filename = "~/.ldapy_connections"

    def __init__ (self):
        """Initializes the ConnectionDataManager, by parsing the file
        containing the recent and saved connections"""
        pass

    @staticmethod
    def _readAndParseFile ():
        """Parses the file specified by ConnectionDataManager.filename and
        returns a tuple:
            (list of recent connections, dictionary of saved connections)"""
        
        try:
            with open(ConnectionDataManager.filename, "r") as f:
                raw = f.read()
                logger.debug("Raw data from %s: %s" % (ConnectionDataManager.filename, raw))
                parsed = json.loads(raw)
                logger.debug("Parsed data from %s: %s" % (ConnectionDataManager.filename, parsed))

                rawRecent = parsed[0]
                recent = []
                for data in rawRecent:
                    recent.append (ConnectionData.load(data))

                rawSaved = parsed[1]
                saved = {}
                for data in rawRecent:
                    name = data["name"]
                    saved[name] = ConnectionData.load(data)

                return (recent, saved)
        except IOError as e:
            logger.warning("Error opening file %s: %s" %
                    (ConnectionDataManager.filename, e))
            return ([], {})

    def addRecentConnection (self, connectionData):
        """Saves a connection to the history of recent connections"""
        pass

    def getRecentConnection (self, N = 1):
        """Retrieves the N:th connection in the history"""
        pass

    def getRecentConnections (self, M = None):
        """Retrieves the recent connections, up to M entries or all if not
        specified"""
        pass


    def saveConnection (self, name, connectionData):
        """Saves a connection to be retrieved by the specified name"""
        pass

    def getConnection (self, name):
        """Retrieves the connection with the specified name"""
        pass

    def getConnections (self):
        """Retrieves all saved connections"""
        pass


