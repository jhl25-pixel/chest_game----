# game_platform/board.py
"""
棋盘基类和具体实现
设计模式：模板方法模式
"""

from abc import ABC, abstractmethod


class Board(ABC):
    """棋盘基类"""
    
    def __init__(self, size):
        if not (8 <= size <= 19):
            raise ValueError("棋盘大小必须在8到19之间")
        self.size = size
        self.grid = [[None for _ in range(size)] for _ in range(size)]
        
    def is_valid_position(self, row, col):
        """检查位置是否在棋盘范围内"""
        return 0 <= row < self.size and 0 <= col < self.size
    
    def is_empty(self, row, col):
        """检查位置是否为空"""
        return self.grid[row][col] is None
    
    def place_stone(self, row, col, color):
        """在指定位置放置棋子"""
        if not self.is_valid_position(row, col):
            raise ValueError("位置超出棋盘范围")
        if not self.is_empty(row, col):
            raise ValueError("该位置已有棋子")
        self.grid[row][col] = color
        
    def remove_stone(self, row, col):
        """移除指定位置的棋子"""
        if self.is_valid_position(row, col):
            self.grid[row][col] = None
            
    def get_stone(self, row, col):
        """获取指定位置的棋子"""
        if self.is_valid_position(row, col):
            return self.grid[row][col]
        return None
    
    def clear(self):
        """清空棋盘"""
        self.grid = [[None for _ in range(self.size)] for _ in range(self.size)]
        
    def is_full(self):
        """检查棋盘是否已满"""
        for row in self.grid:
            if None in row:
                return False
        return True
    
    def copy(self):
        """创建棋盘的深拷贝"""
        new_board = self.__class__(self.size)
        for i in range(self.size):
            for j in range(self.size):
                new_board.grid[i][j] = self.grid[i][j]
        return new_board
    
    def count_stones(self, color):
        """统计某种颜色的棋子数"""
        count = 0
        for i in range(self.size):
            for j in range(self.size):
                if self.grid[i][j] == color:
                    count += 1
        return count


class GomokuBoard(Board):
    """五子棋棋盘"""
    pass


class GoBoard(Board):
    """围棋棋盘"""
    
    def get_adjacent_positions(self, row, col):
        """获取相邻位置"""
        positions = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if self.is_valid_position(new_row, new_col):
                positions.append((new_row, new_col))
        return positions
    
    def get_group(self, row, col):
        """获取棋子所属的棋块"""
        color = self.get_stone(row, col)
        if color is None:
            return set()
        
        group = set()
        to_check = [(row, col)]
        
        while to_check:
            r, c = to_check.pop()
            if (r, c) in group:
                continue
            if self.get_stone(r, c) == color:
                group.add((r, c))
                for adj_pos in self.get_adjacent_positions(r, c):
                    if adj_pos not in group:
                        to_check.append(adj_pos)
        
        return group
    
    def count_liberties(self, row, col):
        """计算棋块的气数"""
        group = self.get_group(row, col)
        liberties = set()
        
        for r, c in group:
            for adj_r, adj_c in self.get_adjacent_positions(r, c):
                if self.is_empty(adj_r, adj_c):
                    liberties.add((adj_r, adj_c))
        
        return len(liberties)
    
    def has_liberties(self, row, col):
        """检查棋块是否有气"""
        return self.count_liberties(row, col) > 0
    
    def remove_captured_stones(self, opponent_color):
        """移除被提掉的对方棋子"""
        captured = []
        for i in range(self.size):
            for j in range(self.size):
                if self.get_stone(i, j) == opponent_color:
                    if not self.has_liberties(i, j):
                        group = self.get_group(i, j)
                        for r, c in group:
                            self.remove_stone(r, c)
                            captured.append((r, c))
        return captured


class OthelloBoard(Board):
    """黑白棋棋盘"""
    
    # 八个方向：上、下、左、右、四个对角线
    DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    def __init__(self, size=8):
        super().__init__(size)
        self._init_board()
    
    def _init_board(self):
        """初始化黑白棋棋盘（中心四子）"""
        mid = self.size // 2
        self.grid[mid-1][mid-1] = 'white'
        self.grid[mid-1][mid] = 'black'
        self.grid[mid][mid-1] = 'black'
        self.grid[mid][mid] = 'white'
    
    def get_valid_moves(self, color):
        """获取所有合法落子位置"""
        valid_moves = []
        for i in range(self.size):
            for j in range(self.size):
                if self.is_valid_move(i, j, color):
                    valid_moves.append((i, j))
        return valid_moves
    
    def is_valid_move(self, row, col, color):
        """检查落子是否合法"""
        if not self.is_valid_position(row, col):
            return False
        if not self.is_empty(row, col):
            return False
        
        opponent = 'white' if color == 'black' else 'black'
        
        for dr, dc in self.DIRECTIONS:
            if self._can_flip_in_direction(row, col, dr, dc, color, opponent):
                return True
        return False
    
    def _can_flip_in_direction(self, row, col, dr, dc, color, opponent):
        """检查某方向是否可以翻转棋子"""
        r, c = row + dr, col + dc
        found_opponent = False
        
        while self.is_valid_position(r, c):
            stone = self.get_stone(r, c)
            if stone == opponent:
                found_opponent = True
            elif stone == color:
                return found_opponent
            else:  # 空位
                return False
            r += dr
            c += dc
        
        return False
    
    def place_and_flip(self, row, col, color):
        """落子并翻转被夹住的棋子，返回被翻转的位置列表"""
        if not self.is_valid_move(row, col, color):
            raise ValueError("非法落子位置")
        
        self.grid[row][col] = color
        flipped = []
        opponent = 'white' if color == 'black' else 'black'
        
        for dr, dc in self.DIRECTIONS:
            flipped.extend(self._flip_in_direction(row, col, dr, dc, color, opponent))
        
        return flipped
    
    def _flip_in_direction(self, row, col, dr, dc, color, opponent):
        """在某方向翻转棋子"""
        to_flip = []
        r, c = row + dr, col + dc
        
        while self.is_valid_position(r, c):
            stone = self.get_stone(r, c)
            if stone == opponent:
                to_flip.append((r, c))
            elif stone == color:
                # 执行翻转
                for fr, fc in to_flip:
                    self.grid[fr][fc] = color
                return to_flip
            else:
                break
            r += dr
            c += dc
        
        return []
    
    def copy(self):
        """创建棋盘的深拷贝"""
        new_board = OthelloBoard(self.size)
        new_board.grid = [[self.grid[i][j] for j in range(self.size)] 
                          for i in range(self.size)]
        return new_board