# game_platform/player.py
"""
玩家类
设计模式：策略模式 - 统一处理人类玩家和AI玩家
"""

from abc import ABC, abstractmethod


class Player(ABC):
    """玩家基类"""
    
    def __init__(self, color, name=None):
        self.color = color
        self.name = name or "玩家"
        self.user = None  # 关联的用户账户
        
    @abstractmethod
    def get_move(self, game):
        """获取下一步落子位置"""
        pass
    
    @abstractmethod
    def is_human(self):
        """是否是人类玩家"""
        pass
    
    def get_display_name(self):
        """获取显示名称"""
        if self.user:
            return f"{self.user.username} ({self.user.wins}胜/{self.user.games}场)"
        return self.name
    
    def set_user(self, user):
        """设置关联的用户账户"""
        self.user = user
        if user:
            self.name = user.username


class HumanPlayer(Player):
    """人类玩家"""
    
    def __init__(self, color, name=None):
        super().__init__(color, name or "玩家")
        self._pending_move = None
        
    def get_move(self, game):
        """获取人类玩家的落子（由外部输入设置）"""
        move = self._pending_move
        self._pending_move = None
        return move
    
    def set_move(self, row, col):
        """设置待落子位置"""
        self._pending_move = (row, col)
    
    def is_human(self):
        return True


class GuestPlayer(HumanPlayer):
    """游客玩家"""
    
    def __init__(self, color):
        super().__init__(color, "游客")


class AIPlayer(Player):
    """AI玩家基类"""
    
    def __init__(self, color, ai_strategy, level=1, name=None):
        super().__init__(color, name or f"AI-Lv{level}")
        self.ai_strategy = ai_strategy
        self.level = level
        
    def get_move(self, game):
        """获取AI的落子"""
        return self.ai_strategy.get_move(game, self.color)
    
    def is_human(self):
        return False
    
    def get_display_name(self):
        """获取显示名称"""
        return f"AI (Lv.{self.level})"


class PlayerFactory:
    """玩家工厂类
    设计模式：工厂模式
    """
    
    @staticmethod
    def create_human_player(color, user=None):
        """创建人类玩家"""
        if user:
            player = HumanPlayer(color, user.username)
            player.set_user(user)
        else:
            player = GuestPlayer(color)
        return player
    
    @staticmethod
    def create_ai_player(color, level, game_type):
        """创建AI玩家"""
        from game_platform.ai import AIFactory
        ai_strategy = AIFactory.create_ai(game_type, level)
        return AIPlayer(color, ai_strategy, level)