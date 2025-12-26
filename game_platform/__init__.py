# game_platform/__init__.py
"""
棋类对战平台

支持游戏类型:
- 五子棋 (Gomoku)
- 围棋 (Go)
- 黑白棋 (Othello/Reversi)

功能特性:
- 多种对战模式 (人人/人机/机机)
- 三级AI算法
- 用户账户管理
- 录像与回放
- 网络对战

设计模式:
- 工厂模式 (Factory)
- 策略模式 (Strategy)
- 模板方法模式 (Template Method)
- 单例模式 (Singleton)
- 外观模式 (Facade)
- 观察者模式 (Observer)
- 组合模式 (Composite)
- 建造者模式 (Builder)
- 命令模式 (Command)
"""

__version__ = '2.0.0'
__author__ = 'Game Platform Team'

from game_platform.platform import GamePlatform
from game_platform.game import Game, GomokuGame, GoGame, OthelloGame
from game_platform.board import Board, GomokuBoard, GoBoard, OthelloBoard
from game_platform.player import Player, HumanPlayer, AIPlayer, PlayerFactory

__all__ = [
    'GamePlatform',
    'Game', 'GomokuGame', 'GoGame', 'OthelloGame',
    'Board', 'GomokuBoard', 'GoBoard', 'OthelloBoard',
    'Player', 'HumanPlayer', 'AIPlayer', 'PlayerFactory',
]