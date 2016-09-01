# -*- coding:utf-8 -*-

import unittest

from flask import current_app
from app import create_app, db


class BasicTestCase(unittest.TestCase):
    # 测试前运行
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    # 测试后运行
    def tearDown(self):
        db.session.remove()
        db.drop_all()   # 注意实际使用的是哪个数据库，开发、测试还是生产，切勿把生产数据库删了...
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)
        
    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
