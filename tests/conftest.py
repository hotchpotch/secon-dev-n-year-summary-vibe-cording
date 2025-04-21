"""pytest構成ファイル"""

from typing import Any

# import pytest # Remove unused import


# 非同期テスト用のマーカーを登録
def pytest_configure(config: Any) -> None:
    """pytestの設定を行う"""
    config.addinivalue_line("markers", "asyncio: mark test as an asyncio test")
