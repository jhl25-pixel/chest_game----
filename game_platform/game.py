# game_platform/game.py
"""
游戏基类和具体实现
设计模式：模板方法模式、策略模式
"""

from abc import ABC, abstractmethod
from game_platform.board import GomokuBoard, GoBoard, OthelloBoard


class Game(ABC):
    """游戏基类"""
    
    def __init__(self, board_size):
        self.board = None
        self.board_size = board_size
        self.current_player = 'black'
        self.game_over = False
        self.winner = None
        self.move_history = []
        
    @abstractmethod
    def make_move(self, row, col):
        """落子"""
        pass
    
    @abstractmethod
    def check_game_over(self):
        """检查游戏是否结束"""
        pass
    
    @abstractmethod
    def get_valid_moves(self):
        """获取当前玩家的所有合法落子位置"""
        pass
    
    def switch_player(self):
        """切换玩家"""
        self.current_player = 'white' if self.current_player == 'black' else 'black'
        
    def undo_move(self):
        """悔棋"""
        if not self.move_history:
            raise ValueError("没有可悔的棋")
        return self._undo_last_move()
    
    @abstractmethod
    def _undo_last_move(self):
        """撤销上一步棋"""
        pass
    
    def resign(self):
        """认输"""
        self.game_over = True
        self.winner = 'white' if self.current_player == 'black' else 'black'
        
    def reset(self, board_size=None):
        """重新开始游戏"""
        if board_size is not None:
            self.board_size = board_size
        self._reset_game()
        
    @abstractmethod
    def _reset_game(self):
        """重置游戏"""
        pass
    
    @abstractmethod
    def save_game(self):
        """保存游戏状态"""
        pass
    
    @abstractmethod
    def load_game(self, game_state):
        """加载游戏状态"""
        pass
    
    def get_game_type(self):
        """获取游戏类型"""
        return self.__class__.__name__.replace('Game', '').lower()


class GomokuGame(Game):
    """五子棋游戏"""
    
    def __init__(self, board_size=15):
        super().__init__(board_size)
        self._reset_game()
        
    def _reset_game(self):
        """重置游戏"""
        self.board = GomokuBoard(self.board_size)
        self.current_player = 'black'
        self.game_over = False
        self.winner = None
        self.move_history = []
    
    def get_valid_moves(self):
        """获取所有合法落子位置"""
        moves = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board.is_empty(i, j):
                    moves.append((i, j))
        return moves
        
    def make_move(self, row, col):
        """落子"""
        if self.game_over:
            raise ValueError("游戏已结束")
        
        self.board.place_stone(row, col, self.current_player)
        self.move_history.append({
            'row': row,
            'col': col,
            'player': self.current_player,
            'type': 'move'
        })
        
        if self._check_five_in_row(row, col):
            self.game_over = True
            self.winner = self.current_player
        elif self.board.is_full():
            self.game_over = True
            self.winner = 'draw'
        else:
            self.switch_player()
            
    def _check_five_in_row(self, row, col):
        """检查是否连成五子"""
        color = self.board.get_stone(row, col)
        if color is None:
            return False
            
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for dr, dc in directions:
            count = 1
            
            r, c = row + dr, col + dc
            while self.board.is_valid_position(r, c) and self.board.get_stone(r, c) == color:
                count += 1
                r += dr
                c += dc
            
            r, c = row - dr, col - dc
            while self.board.is_valid_position(r, c) and self.board.get_stone(r, c) == color:
                count += 1
                r -= dr
                c -= dc
            
            if count >= 5:
                return True
                
        return False
    
    def check_game_over(self):
        """检查游戏是否结束"""
        return self.game_over
    
    def _undo_last_move(self):
        """撤销上一步棋"""
        last_move = self.move_history.pop()
        self.board.remove_stone(last_move['row'], last_move['col'])
        self.game_over = False
        self.winner = None
        self.switch_player()
        return last_move
    
    def save_game(self):
        """保存游戏状态"""
        return {
            'type': 'gomoku',
            'board_size': self.board_size,
            'current_player': self.current_player,
            'game_over': self.game_over,
            'winner': self.winner,
            'board': [[self.board.grid[i][j] for j in range(self.board_size)] 
                     for i in range(self.board_size)],
            'move_history': self.move_history.copy()
        }
    
    def load_game(self, game_state):
        """加载游戏状态"""
        if game_state['type'] != 'gomoku':
            raise ValueError("游戏类型不匹配")
        
        self.board_size = game_state['board_size']
        self.board = GomokuBoard(self.board_size)
        self.current_player = game_state['current_player']
        self.game_over = game_state['game_over']
        self.winner = game_state['winner']
        self.move_history = game_state['move_history'].copy()
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                self.board.grid[i][j] = game_state['board'][i][j]


class GoGame(Game):
    """围棋游戏"""
    
    def __init__(self, board_size=19):
        super().__init__(board_size)
        self.pass_count = 0
        self.ko_point = None
        self.captured_count = {'black': 0, 'white': 0}
        self._reset_game()
        
    def _reset_game(self):
        """重置游戏"""
        self.board = GoBoard(self.board_size)
        self.current_player = 'black'
        self.game_over = False
        self.winner = None
        self.move_history = []
        self.pass_count = 0
        self.ko_point = None
        self.captured_count = {'black': 0, 'white': 0}
    
    def get_valid_moves(self):
        """获取所有合法落子位置"""
        moves = []
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.board.is_empty(i, j):
                    if self.ko_point is None or (i, j) != self.ko_point:
                        moves.append((i, j))
        return moves
        
    def make_move(self, row, col):
        """落子"""
        if self.game_over:
            raise ValueError("游戏已结束")
        
        if self.ko_point and (row, col) == self.ko_point:
            raise ValueError("打劫，不能立即提回")
        
        board_copy = self.board.copy()
        
        self.board.place_stone(row, col, self.current_player)
        
        opponent_color = 'white' if self.current_player == 'black' else 'black'
        captured = self.board.remove_captured_stones(opponent_color)
        
        if captured:
            self.captured_count[self.current_player] += len(captured)
        
        if not self.board.has_liberties(row, col):
            self.board = board_copy
            raise ValueError("不能下在无气的位置")
        
        if len(captured) == 1:
            self.ko_point = captured[0]
        else:
            self.ko_point = None
        
        self.move_history.append({
            'row': row,
            'col': col,
            'player': self.current_player,
            'captured': captured,
            'ko_point': self.ko_point,
            'captured_count': self.captured_count.copy(),
            'type': 'move'
        })
        
        self.pass_count = 0
        self.switch_player()
        
    def pass_move(self):
        """虚着"""
        if self.game_over:
            raise ValueError("游戏已结束")
        
        self.move_history.append({
            'row': None,
            'col': None,
            'player': self.current_player,
            'captured': [],
            'ko_point': None,
            'pass': True,
            'captured_count': self.captured_count.copy(),
            'type': 'pass'
        })
        
        self.pass_count += 1
        self.ko_point = None
        
        if self.pass_count >= 2:
            self._calculate_winner()
            
        self.switch_player()
        
    def _calculate_winner(self):
        """计算胜负（中国规则）"""
        black_score = 0
        white_score = 0
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                stone = self.board.get_stone(i, j)
                if stone == 'black':
                    black_score += 1
                elif stone == 'white':
                    white_score += 1
                else:
                    territory = self._get_territory(i, j)
                    if territory == 'black':
                        black_score += 1
                    elif territory == 'white':
                        white_score += 1
        
        white_score += 3.75
        
        self.game_over = True
        if black_score > white_score:
            self.winner = 'black'
        elif white_score > black_score:
            self.winner = 'white'
        else:
            self.winner = 'draw'
        
        self.final_score = {
            'black': black_score,
            'white': white_score,
        }
            
    def _get_territory(self, row, col):
        """判断空点的归属"""
        if self.board.get_stone(row, col) is not None:
            return None
        
        visited = set()
        to_visit = [(row, col)]
        adjacent_colors = set()
        
        while to_visit:
            r, c = to_visit.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            
            stone = self.board.get_stone(r, c)
            if stone is None:
                for adj_r, adj_c in self.board.get_adjacent_positions(r, c):
                    if (adj_r, adj_c) not in visited:
                        to_visit.append((adj_r, adj_c))
            else:
                adjacent_colors.add(stone)
        
        if len(adjacent_colors) == 1:
            return adjacent_colors.pop()
        return None
    
    def check_game_over(self):
        """检查游戏是否结束"""
        return self.game_over
    
    def _undo_last_move(self):
        """撤销上一步棋"""
        last_move = self.move_history.pop()
        
        if last_move.get('pass'):
            self.pass_count = max(0, self.pass_count - 1)
        else:
            self.board.remove_stone(last_move['row'], last_move['col'])
            
            for r, c in last_move['captured']:
                opponent_color = 'white' if last_move['player'] == 'black' else 'black'
                self.board.place_stone(r, c, opponent_color)
        
        if len(self.move_history) > 0:
            self.captured_count = self.move_history[-1].get('captured_count', {'black': 0, 'white': 0}).copy()
            self.ko_point = self.move_history[-1].get('ko_point')
        else:
            self.captured_count = {'black': 0, 'white': 0}
            self.ko_point = None
        
        self.game_over = False
        self.winner = None
        if hasattr(self, 'final_score'):
            delattr(self, 'final_score')
        self.switch_player()
        return last_move
    
    def save_game(self):
        """保存游戏状态"""
        game_state = {
            'type': 'go',
            'board_size': self.board_size,
            'current_player': self.current_player,
            'game_over': self.game_over,
            'winner': self.winner,
            'pass_count': self.pass_count,
            'ko_point': self.ko_point,
            'captured_count': self.captured_count.copy(),
            'board': [[self.board.grid[i][j] for j in range(self.board_size)] 
                     for i in range(self.board_size)],
            'move_history': self.move_history.copy()
        }
        if hasattr(self, 'final_score'):
            game_state['final_score'] = self.final_score.copy()
        return game_state
    
    def load_game(self, game_state):
        """加载游戏状态"""
        if game_state['type'] != 'go':
            raise ValueError("游戏类型不匹配")
        
        self.board_size = game_state['board_size']
        self.board = GoBoard(self.board_size)
        self.current_player = game_state['current_player']
        self.game_over = game_state['game_over']
        self.winner = game_state['winner']
        self.pass_count = game_state['pass_count']
        self.ko_point = game_state['ko_point']
        self.captured_count = game_state.get('captured_count', {'black': 0, 'white': 0}).copy()
        self.move_history = game_state['move_history'].copy()
        
        if 'final_score' in game_state:
            self.final_score = game_state['final_score'].copy()
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                self.board.grid[i][j] = game_state['board'][i][j]


class OthelloGame(Game):
    """黑白棋游戏"""
    
    def __init__(self, board_size=8):
        super().__init__(board_size)
        self._reset_game()
        
    def _reset_game(self):
        """重置游戏"""
        self.board = OthelloBoard(self.board_size)
        self.current_player = 'black'
        self.game_over = False
        self.winner = None
        self.move_history = []
        self.skip_count = 0
    
    def get_valid_moves(self):
        """获取当前玩家的所有合法落子位置"""
        return self.board.get_valid_moves(self.current_player)
        
    def make_move(self, row, col):
        """落子"""
        if self.game_over:
            raise ValueError("游戏已结束")
        
        if not self.board.is_valid_move(row, col, self.current_player):
            raise ValueError("非法落子位置")
        
        # 记录落子前的棋盘状态
        board_before = [[self.board.grid[i][j] for j in range(self.board_size)] 
                        for i in range(self.board_size)]
        
        flipped = self.board.place_and_flip(row, col, self.current_player)
        
        self.move_history.append({
            'row': row,
            'col': col,
            'player': self.current_player,
            'flipped': flipped,
            'board_before': board_before,
            'type': 'move'
        })
        
        self.skip_count = 0
        self._next_turn()
            
    def pass_move(self):
        """弃权（当没有合法落子位置时）"""
        if self.game_over:
            raise ValueError("游戏已结束")
        
        if self.get_valid_moves():
            raise ValueError("存在合法落子位置，不能弃权")
        
        self.move_history.append({
            'row': None,
            'col': None,
            'player': self.current_player,
            'flipped': [],
            'type': 'pass'
        })
        
        self.skip_count += 1
        self._next_turn()
    
    def _next_turn(self):
        """进行下一回合"""
        self.switch_player()
        
        # 检查游戏是否结束
        if self.board.is_full():
            self._calculate_winner()
            return
        
        # 检查当前玩家是否有合法落子
        if not self.get_valid_moves():
            # 检查对手是否有合法落子
            self.switch_player()
            if not self.get_valid_moves():
                # 双方都无法落子，游戏结束
                self._calculate_winner()
            else:
                # 当前玩家无法落子，但对手可以，自动弃权
                self.switch_player()
                self.skip_count += 1
                if self.skip_count >= 2:
                    self._calculate_winner()
    
    def _calculate_winner(self):
        """计算胜负"""
        black_count = self.board.count_stones('black')
        white_count = self.board.count_stones('white')
        
        self.game_over = True
        self.final_score = {'black': black_count, 'white': white_count}
        
        if black_count > white_count:
            self.winner = 'black'
        elif white_count > black_count:
            self.winner = 'white'
        else:
            self.winner = 'draw'
    
    def check_game_over(self):
        """检查游戏是否结束"""
        return self.game_over
    
    def _undo_last_move(self):
        """撤销上一步棋"""
        if not self.move_history:
            raise ValueError("没有可悔的棋")
        
        last_move = self.move_history.pop()
        
        if last_move['type'] == 'pass':
            self.skip_count = max(0, self.skip_count - 1)
        else:
            # 恢复棋盘状态
            for i in range(self.board_size):
                for j in range(self.board_size):
                    self.board.grid[i][j] = last_move['board_before'][i][j]
        
        self.game_over = False
        self.winner = None
        if hasattr(self, 'final_score'):
            delattr(self, 'final_score')
        self.current_player = last_move['player']
        return last_move
    
    def save_game(self):
        """保存游戏状态"""
        game_state = {
            'type': 'othello',
            'board_size': self.board_size,
            'current_player': self.current_player,
            'game_over': self.game_over,
            'winner': self.winner,
            'skip_count': self.skip_count,
            'board': [[self.board.grid[i][j] for j in range(self.board_size)] 
                     for i in range(self.board_size)],
            'move_history': self.move_history.copy()
        }
        if hasattr(self, 'final_score'):
            game_state['final_score'] = self.final_score.copy()
        return game_state
    
    def load_game(self, game_state):
        """加载游戏状态"""
        if game_state['type'] != 'othello':
            raise ValueError("游戏类型不匹配")
        
        self.board_size = game_state['board_size']
        self.board = OthelloBoard(self.board_size)
        self.current_player = game_state['current_player']
        self.game_over = game_state['game_over']
        self.winner = game_state['winner']
        self.skip_count = game_state.get('skip_count', 0)
        self.move_history = game_state['move_history'].copy()
        
        if 'final_score' in game_state:
            self.final_score = game_state['final_score'].copy()
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                self.board.grid[i][j] = game_state['board'][i][j]