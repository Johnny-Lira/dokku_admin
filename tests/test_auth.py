import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import auth


class VerifyTests(unittest.TestCase):
    def setUp(self):
        self._old = dict(os.environ)
        os.environ.pop(auth.USER_ENV, None)
        os.environ.pop(auth.PASSWORD_ENV, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._old)

    def test_fail_closed_without_credentials(self):
        self.assertFalse(auth.verify("admin", "secret"))

    def test_correct_credentials(self):
        os.environ[auth.USER_ENV] = "admin"
        os.environ[auth.PASSWORD_ENV] = "s3cret"
        self.assertTrue(auth.verify("admin", "s3cret"))

    def test_wrong_password(self):
        os.environ[auth.USER_ENV] = "admin"
        os.environ[auth.PASSWORD_ENV] = "s3cret"
        self.assertFalse(auth.verify("admin", "nope"))

    def test_wrong_user(self):
        os.environ[auth.USER_ENV] = "admin"
        os.environ[auth.PASSWORD_ENV] = "s3cret"
        self.assertFalse(auth.verify("root", "s3cret"))


if __name__ == "__main__":
    unittest.main()
