import unittest
import mock
import json
from ldapy.connection_data import ConnectionDataManager, ConnectionData

class ConnectionDataFormater:
    def __init__ (self, uri = None, bind_dn = None, password = None, name = None):
        things = []

        fmt = '"%s":"%s"'

        self.uri = uri
        if uri:
            things.append(fmt % ("uri", uri))

        self.bind_dn = bind_dn
        if bind_dn:
            things.append(fmt % ("bind_dn", bind_dn))

        self.password = password
        if password:
            things.append(fmt % ("password", password))

        self.name = name
        if name:
            self.json = '"%s":{%s}' % (name, ",".join(things))
        else:
            self.json = '{%s}' % (",".join(things))


    def __repr__ (self):
        return self.json

    @property
    def data (self):
        if self.password:
            return ConnectionData (self.uri, self.bind_dn, self.password)
        else:
            return ConnectionData (self.uri, self.bind_dn)

    @property
    def parsed (self):
        return json.loads(self.json)


class ConnectionDataTests (unittest.TestCase):
    def test_successful_ConnectionData_load (self):
        data = ConnectionDataFormater(
                uri = "ldap://foobar.com",
                bind_dn = "cn=Admin,dc=nodomain",
                password = "ThePassword123")

        connectionData = ConnectionData.load (data.parsed)

        self.assertEqual (data.uri, connectionData.uri)
        self.assertEqual (data.bind_dn, connectionData.bind_dn)
        self.assertEqual (data.password, connectionData.password)

    def test_syntax_error_in_ConnectionData_load (self):
        data = ConnectionDataFormater(
                uri = "ldap://foobar.com",
                password = "ThePassword123")

        with self.assertRaises(SyntaxError):
            connectionData = ConnectionData.load (data.parsed)

class ParserTests (unittest.TestCase):

    def test_successful_trivial_parsing (self):
        trivialData = '{"recent":[],"saved":{}}'

        with mock.patch("__builtin__.open", create=True) as mock_open:
            mock_open.return_value = mock.MagicMock(spec=file)
            f = mock_open.return_value.__enter__.return_value
            f.read.return_value = trivialData

            recent, saved = ConnectionDataManager._readAndParseFile()

            self.assertListEqual([], recent)
            self.assertDictEqual({}, saved)
    
    def test_successful_parsing (self):
        recent1 = ConnectionDataFormater(
                uri = "ldap://recent1.com",
                bind_dn = "cn=recent1")
        recent2 = ConnectionDataFormater(
                uri = "ldap://recent2.com",
                bind_dn = "cn=recent2")
        recentList = [recent1, recent2]
        recentJson = "[%s]" % (",".join([str(r) for r in recentList]))
        expectedRecent = [recent.data for recent in recentList]

        saved1 = ConnectionDataFormater(
                uri = "ldap://saved1.com",
                bind_dn = "cn=saved1",
                name = "saved1")
        saved2 = ConnectionDataFormater(
                uri = "ldap://saved2.com",
                bind_dn = "cn=saved2",
                name = "saved2")
        savedList = [saved1, saved2]
        savedJson = "{%s}" % (",".join([str(s) for s in savedList]))
        expectedSaved = {}
        for saved in savedList:
            expectedSaved[saved.name] = saved.data

        json = '{"recent":%s,"saved":%s}' % (recentJson, savedJson)

        with mock.patch("__builtin__.open", create=True) as mock_open:
            mock_open.return_value = mock.MagicMock(spec=file)
            f = mock_open.return_value.__enter__.return_value
            f.read.return_value = json

            parsedRecent, parsedSaved = ConnectionDataManager._readAndParseFile()

            self.assertListEqual (expectedRecent, parsedRecent)
            self.assertDictEqual (expectedSaved, parsedSaved)

    def test_file_does_not_exist_return_empty_tuple (self):
        with mock.patch("__builtin__.open", create=True) as mock_open:
            mock_open.return_value = mock.MagicMock(spec=file)
            mock_open.return_value.__enter__.side_effect = IOError

            recent, saved = ConnectionDataManager._readAndParseFile()

            self.assertListEqual([], recent)
            self.assertDictEqual({}, saved)

    def parseWithSyntaxError (self, data):
        with mock.patch("__builtin__.open", create=True) as mock_open:
            mock_open.return_value = mock.MagicMock(spec=file)
            f = mock_open.return_value.__enter__.return_value
            f.read.return_value = data

            with self.assertRaises(SyntaxError) as received:
                ConnectionDataManager._readAndParseFile()
            print received.exception

    def test_wrong_outer_type (self):
        self.parseWithSyntaxError ("[]")

    def test_empty_dictionary (self):
        self.parseWithSyntaxError ("{}")
    
    def test_no_recent (self):
        self.parseWithSyntaxError ('{"saved":{}}')

    def test_no_saved (self):
        self.parseWithSyntaxError ('{"recent":[]}')

    def test_recent_wrong_type (self):
        self.parseWithSyntaxError('{"recent":{},"saved":{}}')

    def test_saved_wrong_type (self):
        self.parseWithSyntaxError('{"recent":[],"saved":[]}')

class ConnectionDataManagerTests (unittest.TestCase):
    def test_init (self):
        with mock.patch("ldapy.connection_data.ConnectionDataManager._readAndParseFile",
                spec=ConnectionDataManager._readAndParseFile) as parserMock:
            recentList = ["foo"]
            savedDict = {"bar":"baz"}
            parserMock.return_value = (recentList, savedDict)
            manager = ConnectionDataManager()

            parserMock.assert_called_once_with ()
            self.assertEqual (manager.recent, recentList)
            self.assertEqual (manager.saved, savedDict)

    def test_addRecentConnection (self):
        with mock.patch("ldapy.connection_data.ConnectionDataManager._readAndParseFile",
                spec=ConnectionDataManager._readAndParseFile) as parserMock:

            previousConnection = ConnectionData("ldap://previous.com", "cn=previous")
            nextConnection = ConnectionData("ldap://next.com", "cn=next")

            recentList = [previousConnection]
            savedDict = {}
            parserMock.return_value = (recentList, savedDict)

            manager = ConnectionDataManager()
            manager.addRecentConnection (nextConnection)

            expectedRecent = [nextConnection, previousConnection]
            self.assertListEqual(expectedRecent, manager.recent)

    def test_getRecentConnection_and_getRecentConnections (self):
        connections = []
        N = 10
        for n in range(0,N):
            connections.append(ConnectionData("ldap://%u.com" % n, "cn=%u" % n))

        with mock.patch("ldapy.connection_data.ConnectionDataManager._readAndParseFile",
                spec=ConnectionDataManager._readAndParseFile) as parserMock:
            parserMock.return_value = (connections, {})
            manager = ConnectionDataManager()

            # Test getRecentConnection without arguments
            self.assertEqual(connections[0], manager.getRecentConnection())

            # Test getRecentConnection with arguments
            for n in range(0, N):
                self.assertEqual(connections[n], manager.getRecentConnection(n))

            # Test getRecentConnections
            self.assertListEqual (connections, manager.getRecentConnections())
