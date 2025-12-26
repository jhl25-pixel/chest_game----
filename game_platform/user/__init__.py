# game_platform/user/__init__.py
"""
用户账户管理模块
"""

from game_platform.user.account import User
from game_platform.user.manager import UserManager

__all__ = ['User', 'UserManager']