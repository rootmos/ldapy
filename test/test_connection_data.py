import unittest
import mock
import json
from ldapy.connection_data import ConnectionDataManager, ConnectionData

def unnamed_json (uri, bind_dn, password):
    raw = '{"uri":"%s","bind_dn":"%s","password":"%s"}' % (uri, bind_dn, password)
    return json.loads(raw)

def unnamed_json_without_bind_dn (uri, password):
    raw = '{"uri":"%s","password":"%s"}' % (uri, password)
    return json.loads(raw)

class ParserTests (unittest.TestCase):
    def test_successful_ConnectionData_load (self):
        uri = "ldap://foobar.com"
        bind_dn = "cn=Admin,dc=nodomain"
        password = "ThePassword123"
        data = unnamed_json (uri, bind_dn, password)

        connectionData = ConnectionData.load (data)

        self.assertEqual (uri, connectionData.uri)
        self.assertEqual (bind_dn, connectionData.bind_dn)
        self.assertEqual (password, connectionData.password)

    def test_syntax_error_in_ConnectionData_load (self):
        uri = "ldap://foobar.com"
        password = "ThePassword123"
        data = unnamed_json_without_bind_dn (uri, password)

        with self.assertRaises(SyntaxError) as received:
            connectionData = ConnectionData.load (data)

    def test_successful_trivial_parsing (self):
        trivialData = "[[], {}]"

        with mock.patch("__builtin__.open", create=True) as mock_open:
            mock_open.return_value = mock.MagicMock(spec=file)
            f = mock_open.return_value.__enter__.return_value
            f.read.return_value = trivialData

            recent, saved = ConnectionDataManager._readAndParseFile()

            self.assertListEqual([], recent)
            self.assertDictEqual({}, saved)

    def test_file_does_not_exist_return_empty_tuple (self):
        with mock.patch("__builtin__.open", create=True) as mock_open:
            mock_open.return_value = mock.MagicMock(spec=file)
            mock_open.return_value.__enter__.side_effect = IOError

            recent, saved = ConnectionDataManager._readAndParseFile()

            self.assertListEqual([], recent)
            self.assertDictEqual({}, saved)

