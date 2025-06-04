import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from product_manager import ProductManager
from chat_handler import ChatHandler
from cache_manager import CacheManager
from policy_manager import PolicyManager

class TestSeasonalProducts(unittest.TestCase):
    def setUp(self):
        self.pm = ProductManager()
        # clear cache to ensure fresh load
        if os.path.exists('cache/product_cache.json'):
            os.remove('cache/product_cache.json')
        self.pm.load_product_data()
        self.handler = ChatHandler(product_manager=self.pm,
                                   cache_manager=CacheManager(),
                                   policy_manager=PolicyManager())

    def test_list_all_seasonal(self):
        response = self.handler.handle_chat_message('一共有多少时令水果', 'u1')
        self.assertIn(str(len(self.pm.seasonal_products)), response)
        # ensure multiple items listed
        first_name = self.pm.product_catalog[self.pm.seasonal_products[0]]['name']
        self.assertIn(first_name, response)

if __name__ == '__main__':
    unittest.main()
