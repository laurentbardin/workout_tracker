from django.test import TestCase


class WorksheetTestCase(TestCase):
    def assertHasHeader(self, response, header, msg_prefix=""):
        """
        Assert the response contains a specific header. Matching is
        case-insensitive, i.e. 'content-TYPE' will match 'Content-Type'.
        """
        if msg_prefix:
            msg_prefix += ": "

        self.assertIsNotNone(
            response.get(header),
            f'{msg_prefix}Header "{header}" not found in response.\n'
            f'Available headers: {', '.join(sorted(response.headers.keys()))}'
        )

    def assertHasNotHeader(self, response, header, msg_prefix=""):
        """
        Assert the response does not contain a specific header. Matching is
        case-insensitive, i.e. 'content-TYPE' will match 'Content-Type'.
        """
        if msg_prefix:
            msg_prefix += ": "

        value = response.get(header)
        self.assertIsNone(
            value,
            f'{msg_prefix}Header "{header}" unexpectedly found in response'
        )

    def assertHeaderEqual(self, response, header, expected, msg_prefix=None):
        if msg_prefix:
            msg_prefix += ": "

        self.assertHasHeader(response, header, msg_prefix)
        self.assertEqual(response.get(header), expected, msg_prefix)

    def assertHeaderJSONEqual(self, response, header, expected, msg_prefix=None):
        if msg_prefix:
            msg_prefix += ": "

        self.assertHasHeader(response, header, msg_prefix)
        self.assertJSONEqual(response.get(header), expected, msg_prefix)
