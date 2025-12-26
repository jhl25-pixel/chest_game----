# game_platform/ai/__init__.py
"""
AI模块
"""

from game_platform.ai.base import AIStrategy
from game_platform.ai.factory import AIFactory
from game_platform.ai.random_ai import RandomAI
from game_platform.ai.eval_ai import EvalAI
from game_platform.ai.mcts_ai import MCTSAI

__all__ = ['AIStrategy', 'AIFactory', 'RandomAI', 'EvalAI', 'MCTSAI']