import unittest
import mock
import json
import string
from ldapy.connection_data import *

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

    def createConnectionData (self, token):
        return ConnectionData("ldap://%s.com" % str(token), "cn=%s" % str(token))

    def createConnectionManager (self, numOfRecent = 0, numOfSaved = 0):
        recent = []
        for n in range(0, numOfRecent):
            recent.append(self.createConnectionData(n))

        saved = {}
        for c in string.lowercase[:numOfSaved]:
            saved[c] = self.createConnectionData(c)

        with mock.patch("ldapy.connection_data.ConnectionDataManager._readAndParseFile",
                spec=ConnectionDataManager._readAndParseFile) as parserMock:
            parserMock.return_value = (recent, saved)
            manager = ConnectionDataManager()

        self.assertListEqual (recent, manager.recent)
        self.assertDictEqual (saved, manager.saved)
        return manager, list(recent), dict(saved)


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
        manager, recent, saved = self.createConnectionManager (numOfRecent = 1)

        newConnection = self.createConnectionData ("new")
        manager.addRecentConnection (newConnection)

        recent.insert(0, newConnection)
        self.assertListEqual(recent, manager.recent)
        self.assertDictEqual(saved, manager.saved)

    def test_getRecentConnection_and_getRecentConnections (self):
        N = 10
        manager, connections, _ = self.createConnectionManager (numOfRecent = N)

        # Test getRecentConnection without arguments
        self.assertEqual(connections[0], manager.getRecentConnection())

        # Test getRecentConnection with arguments
        for n in range(0, N):
            self.assertEqual(connections[n], manager.getRecentConnection(n))

        # Test getRecentConnections without arguments
        self.assertListEqual (connections, manager.getRecentConnections())

        # Test getRecentConnection with arguments
        for n in range(0, N):
            self.assertListEqual (connections[:n], manager.getRecentConnections(n)) 

    def test_getRecentConnection_with_too_large_number (self):
        N = 2
        manager, _, _ = self.createConnectionManager (numOfRecent = N - 1)

        with self.assertRaises (NoSuchRecentConnection) as received:
            manager.getRecentConnection (N)

        msg = NoSuchRecentConnection._msg % ordinal (N)
        self.assertEqual (msg, str(received.exception))

    def test_saveConnection (self):
        manager, recent, saved = self.createConnectionManager (numOfSaved = 1)

        newKey = "new"
        newConnection = self.createConnectionData (newKey)

        manager.saveConnection (newKey, newConnection)

        saved[newKey] = newConnection
        self.assertListEqual(recent, manager.recent)
        self.assertDictEqual(saved, manager.saved)

    def test_removeConnection (self):
        manager, recent, saved = self.createConnectionManager (numOfSaved = 3)

        delKey = "b"
        manager.removeConnection (delKey)

        del saved[delKey]
        self.assertListEqual(recent, manager.recent)
        self.assertDictEqual(saved, manager.saved)

    def test_remove_nonexistent_connection (self):
        manager, _, _ = self.createConnectionManager ()

        with self.assertRaises (NoSuchSavedConnection):
            manager.removeConnection ("b")

    def test_getConnection (self):
        manager, _, saved = self.createConnectionManager (numOfSaved = 3)

        key = "b"
        self.assertEqual (saved[key], manager.getConnection(key))

    def test_getConnection_for_nonexistent_name (self):
        manager, _, _ = self.createConnectionManager ()

        key = "c"
        with self.assertRaises (NoSuchSavedConnection) as received:
            manager.getConnection (key)

        msg = NoSuchSavedConnection._msg % key
        self.assertEqual (msg, str(received.exception))
        
    def test_getConnections (self):
        manager, _, saved = self.createConnectionManager (numOfSaved = 3)
        self.assertDictEqual (saved, manager.getConnections())


class OrdinalsTest (unittest.TestCase):
    def test_ordinals (self):
        tests = [(1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"),
                 (12, "12th"), (13, "13th"),
                 (22, "22nd"), (23, "23rd"), (24, "24th")]
        for n, s in tests:
            self.assertEqual (s, ordinal(n))

