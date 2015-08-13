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
        """Converts a dictionary to a ConnectionData object"""
        try:
            if "password" in data:
                return ConnectionData (data["uri"], data["bind_dn"], data["password"])
            else:
                return ConnectionData (data["uri"], data["bind_dn"])
        except KeyError, key:
            raise SyntaxError("Syntax error parsing connection data: no %s field" % key)

    def save (self):
        """Converts this ConnectionData object to a dictionary"""
        data = {"uri": self.uri, "bind_dn": self.bind_dn}

        if self.password:
            data["password"] = self.password

        return data

    def __eq__ (self, other):
        return isinstance(other, self.__class__) and \
                self.uri == other.uri and \
                self.bind_dn == other.bind_dn and \
                self.password == other.password



class ConnectionDataManagerError (Exception):
    def __str__ (self):
        return str(self.msg)

def ordinal (i):
    """Written by Garet @ http://codegolf.stackexchange.com/questions/4707/outputting-ordinal-numbers-1st-2nd-3rd#answer-4712"""
    k=i%10
    return "%d%s"%(i,"tsnrhtdd"[(i/10%10!=1)*(k<4)*k::4])

class NoSuchRecentConnection (ConnectionDataManagerError):
    _msg = "The %s most recent connection does not exist"
    def __init__ (self, N):
        self.msg = NoSuchRecentConnection._msg % ordinal (N)

class NoSuchSavedConnection (ConnectionDataManagerError):
    _msg = "No saved connection with name: %s"
    def __init__ (self, name):
        self.msg = NoSuchSavedConnection._msg  % name


class ConnectionDataManager:
    """A class for managing ConnectionData items for recent and saved
    connections"""

    filename = "~/.ldapy_connections"

    def __init__ (self):
        """Initializes the ConnectionDataManager, by parsing the file
        containing the recent and saved connections"""

        self.recent, self.saved = ConnectionDataManager._readAndParseFile()

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
                if not isinstance(parsed, dict):
                    raise SyntaxError("Syntax error: outer element should be a dictionary (containing 'recent' and 'saved' elements)")
                logger.debug("Parsed data from %s: %s" % (ConnectionDataManager.filename, parsed))

                # Parse the recent connections
                rawRecent = parsed["recent"]
                if not isinstance(rawRecent, list):
                    raise SyntaxError("Syntax error: recent element should be a list")

                recent = []
                for data in rawRecent:
                    recent.append (ConnectionData.load(data))

                # Parse the saved connections
                rawSaved = parsed["saved"]
                print rawSaved
                if not isinstance(rawSaved, dict):
                    raise SyntaxError("Syntax error: saved element should be a dictionary")

                saved = {}
                for name, data in rawSaved.iteritems():
                    saved[name] = ConnectionData.load(data)

                return (recent, saved)
        except KeyError, key:
            raise SyntaxError("Syntax error parsing connection data: no %s field" % key)
        except IOError as e:
            logger.warning("Error opening file %s: %s" %
                    (ConnectionDataManager.filename, e))
            return ([], {})

    def addRecentConnection (self, connectionData):
        """Saves a connection to the history of recent connections"""
        self.recent.insert(0, connectionData)

    def getRecentConnection (self, N = 0):
        """Retrieves the N:th connection in the history"""
        try:
            return self.recent[N]
        except IndexError:
            raise NoSuchRecentConnection (N)

    def getRecentConnections (self, M = None):
        """Retrieves the recent connections, up to M entries or all if not
        specified"""
        if M is None:
            return self.recent
        else:
            return self.recent[:M]


    def saveConnection (self, name, connectionData):
        """Saves a connection to be retrieved by the specified name"""
        self.saved[name] = connectionData
    
    def removeConnection (self, name):
        """Removes a previously saved connection by the specified name"""
        try:
            del self.saved[name]
        except KeyError:
            raise NoSuchSavedConnection (name)

    def getConnection (self, name):
        """Retrieves the connection with the specified name"""
        try:
            return self.saved[name]
        except KeyError:
            raise NoSuchSavedConnection (name)

    def getConnections (self):
        """Retrieves all saved connections"""
        return self.saved


