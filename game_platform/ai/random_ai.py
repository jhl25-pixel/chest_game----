# game_platform/ai/random_ai.py
"""
一级AI：随机落子
"""

import random
from game_platform.ai.base import AIStrategy


class RandomAI(AIStrategy):
    """随机AI - 一级AI"""
    
    def get_move(self, game, color):
        """随机选择一个合法位置落子"""
        valid_moves = game.get_valid_moves()
        
        if not valid_moves:
            return None
        
        return random.choice(valid_moves)
    
    def get_level(self):
        return 1