# game_platform/ai/base.py
"""
AI策略基类
"""

from abc import ABC, abstractmethod


class AIStrategy(ABC):
    """AI策略基类"""
    
    @abstractmethod
    def get_move(self, game, color):
        """获取AI的落子位置"""
        pass
    
    @abstractmethod
    def get_level(self):
        """获取AI等级"""
        pass