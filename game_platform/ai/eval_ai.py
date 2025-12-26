# game_platform/ai/eval_ai.py
"""
二级AI：基于评估函数的AI
使用位置权重和翻转数量进行评估
"""

from game_platform.ai.base import AIStrategy
from game_platform.game import OthelloGame, GomokuGame


class EvalAI(AIStrategy):
    """评估函数AI - 二级AI"""
    
    # 黑白棋位置权重表（8x8）
    OTHELLO_WEIGHTS = [
        [100, -20,  10,   5,   5,  10, -20, 100],
        [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
        [ 10,  -2,   1,   1,   1,   1,  -2,  10],
        [  5,  -2,   1,   0,   0,   1,  -2,   5],
        [  5,  -2,   1,   0,   0,   1,  -2,   5],
        [ 10,  -2,   1,   1,   1,   1,  -2,  10],
        [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
        [100, -20,  10,   5,   5,  10, -20, 100],
    ]
    
    def get_move(self, game, color):
        """选择评估分数最高的位置"""
        valid_moves = game.get_valid_moves()
        
        if not valid_moves:
            return None
        
        if isinstance(game, OthelloGame):
            return self._get_othello_move(game, color, valid_moves)
        elif isinstance(game, GomokuGame):
            return self._get_gomoku_move(game, color, valid_moves)
        else:
            # 默认选择第一个合法位置
            return valid_moves[0]
    
    def _get_othello_move(self, game, color, valid_moves):
        """黑白棋落子策略"""
        best_move = None
        best_score = float('-inf')
        
        for row, col in valid_moves:
            score = self._evaluate_othello_move(game, row, col, color)
            if score > best_score:
                best_score = score
                best_move = (row, col)
        
        return best_move
    
    def _evaluate_othello_move(self, game, row, col, color):
        """评估黑白棋落子
        
        考虑因素：
        1. 位置权重
        2. 翻转棋子数
        3. 稳定性（角落和边）
        """
        # 创建棋盘副本进行模拟
        board_copy = game.board.copy()
        flipped = board_copy.place_and_flip(row, col, color)
        
        score = 0
        
        # 位置权重
        if row < 8 and col < 8:
            score += self.OTHELLO_WEIGHTS[row][col]
        
        # 翻转数量奖励
        score += len(flipped) * 2
        
        # 角落奖励
        corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
        if (row, col) in corners:
            score += 50
        
        # 靠近角落的位置惩罚（如果角落还是空的）
        dangerous_positions = {
            (0, 0): [(0, 1), (1, 0), (1, 1)],
            (0, 7): [(0, 6), (1, 6), (1, 7)],
            (7, 0): [(6, 0), (6, 1), (7, 1)],
            (7, 7): [(6, 6), (6, 7), (7, 6)],
        }
        
        for corner, danger_list in dangerous_positions.items():
            if game.board.is_empty(corner[0], corner[1]):
                if (row, col) in danger_list:
                    score -= 30
        
        # 行动力（模拟落子后对手的合法位置数）
        opponent = 'white' if color == 'black' else 'black'
        opponent_moves = len(board_copy.get_valid_moves(opponent))
        score -= opponent_moves * 1.5
        
        return score
    
    def _get_gomoku_move(self, game, color, valid_moves):
        """五子棋落子策略"""
        best_move = None
        best_score = float('-inf')
        
        opponent = 'white' if color == 'black' else 'black'
        
        for row, col in valid_moves:
            # 进攻分数
            attack_score = self._evaluate_gomoku_position(game, row, col, color)
            # 防守分数
            defense_score = self._evaluate_gomoku_position(game, row, col, opponent)
            
            # 综合评分：进攻略重于防守
            score = attack_score * 1.1 + defense_score
            
            if score > best_score:
                best_score = score
                best_move = (row, col)
        
        return best_move
    
    def _evaluate_gomoku_position(self, game, row, col, color):
        """评估五子棋某位置的分数"""
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count, open_ends = self._count_in_direction(game, row, col, dr, dc, color)
            
            # 根据连子数和开放端评分
            if count >= 5:
                score += 100000
            elif count == 4:
                if open_ends == 2:
                    score += 10000  # 活四
                elif open_ends == 1:
                    score += 1000   # 冲四
            elif count == 3:
                if open_ends == 2:
                    score += 1000   # 活三
                elif open_ends == 1:
                    score += 100    # 眠三
            elif count == 2:
                if open_ends == 2:
                    score += 100    # 活二
                elif open_ends == 1:
                    score += 10     # 眠二
        
        # 中心位置加分
        center = game.board_size // 2
        dist = abs(row - center) + abs(col - center)
        score += max(0, 10 - dist)
        
        return score
    
    def _count_in_direction(self, game, row, col, dr, dc, color):
        """计算某方向上的连子数和开放端数"""
        count = 1
        open_ends = 0
        
        # 正方向
        r, c = row + dr, col + dc
        while game.board.is_valid_position(r, c) and game.board.get_stone(r, c) == color:
            count += 1
            r += dr
            c += dc
        if game.board.is_valid_position(r, c) and game.board.is_empty(r, c):
            open_ends += 1
        
        # 反方向
        r, c = row - dr, col - dc
        while game.board.is_valid_position(r, c) and game.board.get_stone(r, c) == color:
            count += 1
            r -= dr
            c -= dc
        if game.board.is_valid_position(r, c) and game.board.is_empty(r, c):
            open_ends += 1
        
        return count, open_ends
    
    def get_level(self):
        return 2