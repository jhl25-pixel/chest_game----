# game_platform/ai/factory.py
"""
AI工厂类
设计模式：工厂模式
"""

from game_platform.ai.random_ai import RandomAI
from game_platform.ai.eval_ai import EvalAI
from game_platform.ai.mcts_ai import MCTSAI


class AIFactory:
    """AI工厂"""
    
    # AI等级到类的映射
    AI_CLASSES = {
        1: RandomAI,
        2: EvalAI,
        3: MCTSAI,
    }
    
    # 支持AI的游戏类型
    SUPPORTED_GAMES = ['othello', 'gomoku', 'go']
    
    @classmethod
    def create_ai(cls, game_type, level):
        """创建AI实例
        
        Args:
            game_type: 游戏类型 ('othello', 'gomoku')
            level: AI等级 (1-3)
            
        Returns:
            AIStrategy: AI实例
        """
        if game_type not in cls.SUPPORTED_GAMES:
            raise ValueError(f"游戏类型 {game_type} 不支持AI")
        
        if level not in cls.AI_CLASSES:
            raise ValueError(f"不支持的AI等级: {level}")
        
        ai_class = cls.AI_CLASSES[level]
        return ai_class()
    
    @classmethod
    def get_available_levels(cls):
        """获取可用的AI等级列表"""
        return list(cls.AI_CLASSES.keys())
    
    @classmethod
    def get_level_description(cls, level):
        """获取AI等级描述"""
        descriptions = {
            1: "随机AI - 随机选择合法位置落子",
            2: "评估AI - 使用评估函数选择最优位置",
            3: "MCTS AI - 使用蒙特卡洛树搜索"
        }
        return descriptions.get(level, "未知等级")