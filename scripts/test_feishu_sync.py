#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feishu_sync.py 里不碰网络的那部分：块匹配和 multipart 拼装。"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import feishu_sync


class FindFileBlockTest(unittest.TestCase):
    def test_matches_file_block_by_name(self):
        blocks = [
            {"block_id": "b1", "block_type": 2, "text": {"elements": []}},
            {"block_id": "b2", "block_type": 23, "file": {"name": "a.pdf", "token": "t1"}},
            {"block_id": "b3", "block_type": 23, "file": {"name": "b.pdf", "token": "t2"}},
        ]
        self.assertEqual(feishu_sync.find_file_block(blocks, "b.pdf"), "b3")

    def test_ignores_unnamed_wrapper(self):
        blocks = [
            {"block_id": "wrap", "block_type": 33, "children": ["inner"]},
            {"block_id": "inner", "block_type": 23, "file": {"name": "", "token": ""}},
            {"block_id": "filled", "block_type": 23, "file": {"name": "a.pdf", "token": "t"}},
        ]
        self.assertEqual(feishu_sync.find_file_block(blocks, "a.pdf"), "filled")

    def test_returns_none_when_missing(self):
        blocks = [{"block_id": "b", "block_type": 23, "file": {"name": "a.pdf"}}]
        self.assertIsNone(feishu_sync.find_file_block(blocks, "missing.pdf"))


class MultipartTest(unittest.TestCase):
    def test_includes_fields_and_file_bytes(self):
        boundary, body = feishu_sync.encode_multipart(
            {"file_name": "产品手册.pdf", "size": "3"}, "产品手册.pdf", b"%PDF-1.5"
        )
        text = body.decode("utf-8")
        self.assertIn(f"--{boundary}", text)
        self.assertIn('name="file_name"', text)
        self.assertIn("产品手册.pdf", text)
        self.assertIn("%PDF-1.5", text)
        self.assertTrue(text.endswith(f"--{boundary}--\r\n"))

    def test_ascii_filename_avoids_header_encoding_error(self):
        _, body = feishu_sync.encode_multipart({"file_name": "产品手册.pdf"}, "产品手册.pdf", b"x")
        self.assertIn('filename="upload.pdf"', body.decode("utf-8"))


class TenantTokenTest(unittest.TestCase):
    def test_token_request_carries_no_authorization_header(self):
        """取 token 的请求本身不能带 Authorization，否则拼字符串时拿到 None。"""
        captured = {}

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"code": 0, "tenant_access_token": "t-123"}'

        def fake_urlopen(req, timeout=0):
            captured["req"] = req
            return FakeResponse()

        with mock.patch("feishu_sync.urllib.request.urlopen", fake_urlopen):
            self.assertEqual(feishu_sync.tenant_token("cli_x", "secret"), "t-123")
        self.assertIsNone(captured["req"].get_header("Authorization"))


if __name__ == "__main__":
    unittest.main()
