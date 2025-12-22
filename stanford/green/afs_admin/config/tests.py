import unittest

from stanford.green.afs_admin.config import AFSConfig

class TestAFSConfig(unittest.TestCase):

    def test_basic(self) -> None:
        self.assertTrue(True)

    def test_config_basic(self) -> None:
        config = AFSConfig()
        config_dict = config.to_dict()
        self.assertIn('cell', config_dict)
        self.assertEqual(config.cell, None)

        config = AFSConfig(
            cell='my.example.com'
        )
        config_dict = config.to_dict()
        self.assertEqual(config.cell, 'my.example.com')
