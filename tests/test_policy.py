import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app.policy.manager import PolicyManager
from src.app.chat.handler import ChatHandler
from src.app.products.manager import ProductManager
from src.core.cache import CacheManager

class TestPolicyQuestion(unittest.TestCase):
    def setUp(self):
        self.pm = ProductManager()
        self.pm.load_product_data()
        self.policy = PolicyManager()
        self.handler = ChatHandler(product_manager=self.pm,
                                   policy_manager=self.policy,
                                   cache_manager=CacheManager())

    def test_delivery_question(self):
        response = self.handler.handle_chat_message('配送时间是什么时候', 'u1')
        self.assertIn('星期三截单星期五送货', response)

if __name__ == '__main__':
    unittest.main()
