# game_platform/ai/mcts_ai.py
"""三级AI：Alpha-Beta剪枝搜索（修复版v3 - 修复连五检测）"""
from game_platform.ai.base import AIStrategy
from game_platform.game import OthelloGame, GomokuGame
import random


class MCTSAI(AIStrategy):
    """Alpha-Beta搜索AI - 三级AI"""
    
    def __init__(self, max_depth=4):
        self.max_depth = max_depth
        
    def get_level(self):
        return 3
    
    def get_move(self, game, color):
        """获取最佳走法"""
        if isinstance(game, GomokuGame):
            return self._get_gomoku_move(game, color)
        elif isinstance(game, OthelloGame):
            return self._get_othello_move(game, color)
        else:
            valid_moves = game.get_valid_moves()
            return random.choice(valid_moves) if valid_moves else None
    
    def _get_gomoku_move(self, game, color):
        """五子棋：优先级检测 + Alpha-Beta搜索"""
        board = game.board
        size = board.size
        opponent = 'white' if color == 'black' else 'black'
        
        print(f"\n[AI Lv3] === 轮到 {color} 落子 ===")
        
        # ========== 最高优先级：自己能连五必走 ==========
        win_moves = self._find_all_winning_moves(board, size, color)
        if win_moves:
            print(f"[AI Lv3] ★★★ 找到获胜点: {win_moves[0]} (共{len(win_moves)}个)")
            return win_moves[0]
        
        # ========== 第二优先级：对手能连五必挡 ==========
        opp_win_moves = self._find_all_winning_moves(board, size, opponent)
        if opp_win_moves:
            print(f"[AI Lv3] !!! 必须阻挡对手连五: {opp_win_moves[0]}")
            return opp_win_moves[0]
        
        # ========== 第三优先级：自己能形成活四（必胜） ==========
        my_open_four = self._find_open_four(board, size, color)
        if my_open_four:
            print(f"[AI Lv3] ★★ 形成活四: {my_open_four}")
            return my_open_four
        
        # ========== 第四优先级：对手能形成活四必挡 ==========
        opp_open_four = self._find_open_four(board, size, opponent)
        if opp_open_four:
            print(f"[AI Lv3] !! 阻挡对手活四: {opp_open_four}")
            return opp_open_four
        
        # ========== 第五优先级：自己能形成冲四 ==========
        my_rush_four = self._find_rush_four(board, size, color)
        if my_rush_four:
            print(f"[AI Lv3] ★ 形成冲四: {my_rush_four}")
            return my_rush_four
        
        # ========== 第六优先级：对手能形成冲四必挡 ==========
        opp_rush_four = self._find_rush_four(board, size, opponent)
        if opp_rush_four:
            print(f"[AI Lv3] ! 阻挡对手冲四: {opp_rush_four}")
            return opp_rush_four
        
        # ========== 第七优先级：自己双活三 ==========
        my_double_three = self._find_double_three(board, size, color)
        if my_double_three:
            print(f"[AI Lv3] 形成双活三: {my_double_three}")
            return my_double_three
        
        # ========== 第八优先级：对手双活三必挡 ==========
        opp_double_three = self._find_double_three(board, size, opponent)
        if opp_double_three:
            print(f"[AI Lv3] 阻挡对手双活三: {opp_double_three}")
            return opp_double_three
        
        # ========== 搜索阶段 ==========
        candidates = self._get_candidate_moves(board, size)
        if not candidates:
            center = size // 2
            return (center, center)
        
        if len(candidates) == 1:
            return candidates[0]
        
        # 排序并限制搜索宽度
        candidates = self._sort_moves(board, size, candidates, color, opponent)[:15]
        
        # Alpha-Beta搜索
        best_score = float('-inf')
        best_move = candidates[0]
        
        for move in candidates:
            board.grid[move[0]][move[1]] = color
            score = self._alphabeta(board, size, self.max_depth - 1, 
                                   float('-inf'), float('inf'), 
                                   False, color, opponent)
            board.grid[move[0]][move[1]] = None
            
            if score > best_score:
                best_score = score
                best_move = move
        
        print(f"[AI Lv3] 搜索选择: {best_move}, 评分: {best_score}")
        return best_move
    
    def _find_all_winning_moves(self, board, size, color):
        """找出所有能连成5子的点（全方向扫描）"""
        winning_moves = []
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for i in range(size):
            for j in range(size):
                # 跳过非空位置
                if board.grid[i][j] is not None:
                    continue
                
                # 检查每个方向
                for dr, dc in directions:
                    count = 1  # 包含当前空位
                    
                    # 正向计数
                    r, c = i + dr, j + dc
                    while 0 <= r < size and 0 <= c < size and board.grid[r][c] == color:
                        count += 1
                        r, c = r + dr, c + dc
                    
                    # 反向计数
                    r, c = i - dr, j - dc
                    while 0 <= r < size and 0 <= c < size and board.grid[r][c] == color:
                        count += 1
                        r, c = r - dr, c - dc
                    
                    # 如果能形成5连或更多
                    if count >= 5:
                        winning_moves.append((i, j))
                        break  # 这个点已经是获胜点，不用检查其他方向
        
        return winning_moves
    
    def _find_open_four(self, board, size, color):
        """找活四点（落子后形成两端都开放的四连）"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for i in range(size):
            for j in range(size):
                if board.grid[i][j] is not None:
                    continue
                
                for dr, dc in directions:
                    count = 1
                    open_ends = 0
                    
                    # 正向
                    r, c = i + dr, j + dc
                    while 0 <= r < size and 0 <= c < size and board.grid[r][c] == color:
                        count += 1
                        r, c = r + dr, c + dc
                    # 检查正向端点是否开放
                    if 0 <= r < size and 0 <= c < size and board.grid[r][c] is None:
                        open_ends += 1
                    
                    # 反向
                    r, c = i - dr, j - dc
                    while 0 <= r < size and 0 <= c < size and board.grid[r][c] == color:
                        count += 1
                        r, c = r - dr, c - dc
                    # 检查反向端点是否开放
                    if 0 <= r < size and 0 <= c < size and board.grid[r][c] is None:
                        open_ends += 1
                    
                    # 活四：4子且两端开放
                    if count == 4 and open_ends == 2:
                        return (i, j)
        
        return None
    
    def _find_rush_four(self, board, size, color):
        """找冲四点（落子后形成至少一端开放的四连）"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for i in range(size):
            for j in range(size):
                if board.grid[i][j] is not None:
                    continue
                
                for dr, dc in directions:
                    count = 1
                    open_ends = 0
                    
                    # 正向
                    r, c = i + dr, j + dc
                    while 0 <= r < size and 0 <= c < size and board.grid[r][c] == color:
                        count += 1
                        r, c = r + dr, c + dc
                    if 0 <= r < size and 0 <= c < size and board.grid[r][c] is None:
                        open_ends += 1
                    
                    # 反向
                    r, c = i - dr, j - dc
                    while 0 <= r < size and 0 <= c < size and board.grid[r][c] == color:
                        count += 1
                        r, c = r - dr, c - dc
                    if 0 <= r < size and 0 <= c < size and board.grid[r][c] is None:
                        open_ends += 1
                    
                    # 冲四：4子且至少一端开放（不是活四的情况）
                    if count == 4 and open_ends == 1:
                        return (i, j)
        
        return None
    
    def _find_double_three(self, board, size, color):
        """找双活三点"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for i in range(size):
            for j in range(size):
                if board.grid[i][j] is not None:
                    continue
                
                open_threes = 0
                for dr, dc in directions:
                    count = 1
                    open_ends = 0
                    
                    r, c = i + dr, j + dc
                    while 0 <= r < size and 0 <= c < size and board.grid[r][c] == color:
                        count += 1
                        r, c = r + dr, c + dc
                    if 0 <= r < size and 0 <= c < size and board.grid[r][c] is None:
                        open_ends += 1
                    
                    r, c = i - dr, j - dc
                    while 0 <= r < size and 0 <= c < size and board.grid[r][c] == color:
                        count += 1
                        r, c = r - dr, c - dc
                    if 0 <= r < size and 0 <= c < size and board.grid[r][c] is None:
                        open_ends += 1
                    
                    # 活三：3子且两端开放
                    if count == 3 and open_ends == 2:
                        open_threes += 1
                
                if open_threes >= 2:
                    return (i, j)
        
        return None
    
    def _alphabeta(self, board, size, depth, alpha, beta, is_maximizing, my_color, opponent):
        """Alpha-Beta剪枝搜索"""
        current = my_color if is_maximizing else opponent
        other = opponent if is_maximizing else my_color
        
        # 检查是否有人获胜
        winner = self._check_winner(board, size)
        if winner == my_color:
            return 100000 + depth
        elif winner == opponent:
            return -100000 - depth
        
        # 深度限制
        if depth == 0:
            return self._evaluate_board(board, size, my_color, opponent)
        
        # 获取候选走法
        candidates = self._get_candidate_moves(board, size)
        if not candidates:
            return self._evaluate_board(board, size, my_color, opponent)
        
        # 紧急走法优先
        win_move = self._find_all_winning_moves(board, size, current)
        if win_move:
            candidates = win_move + [m for m in candidates if m not in win_move]
        
        block_move = self._find_all_winning_moves(board, size, other)
        if block_move:
            for m in block_move:
                if m not in candidates[:5]:
                    candidates.insert(0, m)
        
        candidates = self._sort_moves(board, size, candidates, current, other)[:12]
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in candidates:
                board.grid[move[0]][move[1]] = current
                eval_score = self._alphabeta(board, size, depth - 1, alpha, beta, False, my_color, opponent)
                board.grid[move[0]][move[1]] = None
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in candidates:
                board.grid[move[0]][move[1]] = current
                eval_score = self._alphabeta(board, size, depth - 1, alpha, beta, True, my_color, opponent)
                board.grid[move[0]][move[1]] = None
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def _check_winner(self, board, size):
        """检查是否有人获胜"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        
        for i in range(size):
            for j in range(size):
                stone = board.grid[i][j]
                if not stone:
                    continue
                
                for dr, dc in directions:
                    count = 1
                    r, c = i + dr, j + dc
                    while 0 <= r < size and 0 <= c < size and board.grid[r][c] == stone:
                        count += 1
                        r, c = r + dr, c + dc
                    
                    if count >= 5:
                        return stone
        return None
    
    def _get_candidate_moves(self, board, size):
        """获取候选走法（棋子附近的空位）"""
        neighbors = set()
        has_stones = False
        
        for i in range(size):
            for j in range(size):
                if board.grid[i][j]:
                    has_stones = True
                    for di in range(-2, 3):
                        for dj in range(-2, 3):
                            ni, nj = i + di, j + dj
                            if 0 <= ni < size and 0 <= nj < size:
                                if board.grid[ni][nj] is None:
                                    neighbors.add((ni, nj))
        
        if not has_stones:
            center = size // 2
            return [(center, center)]
        
        return list(neighbors)
    
    def _sort_moves(self, board, size, moves, color, opponent):
        """按启发式评分排序"""
        scored = []
        for move in moves:
            score = self._evaluate_move(board, size, move, color, opponent)
            scored.append((score, move))
        scored.sort(reverse=True)
        return [m for _, m in scored]
    
    def _evaluate_move(self, board, size, move, color, opponent):
        """评估单个走法"""
        row, col = move
        
        # 进攻分
        attack = self._count_line_score(board, size, row, col, color)
        # 防守分（权重更高）
        defense = self._count_line_score(board, size, row, col, opponent) * 1.2
        
        # 中心加分
        center = size // 2
        dist = abs(row - center) + abs(col - center)
        center_bonus = max(0, 8 - dist)
        
        return attack + defense + center_bonus
    
    def _count_line_score(self, board, size, row, col, color):
        """计算某位置某颜色的线型分数"""
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        total_score = 0
        
        for dr, dc in directions:
            count = 1
            open_ends = 0
            
            # 正向
            r, c = row + dr, col + dc
            while 0 <= r < size and 0 <= c < size and board.grid[r][c] == color:
                count += 1
                r, c = r + dr, c + dc
            if 0 <= r < size and 0 <= c < size and board.grid[r][c] is None:
                open_ends += 1
            
            # 反向
            r, c = row - dr, col - dc
            while 0 <= r < size and 0 <= c < size and board.grid[r][c] == color:
                count += 1
                r, c = r - dr, c - dc
            if 0 <= r < size and 0 <= c < size and board.grid[r][c] is None:
                open_ends += 1
            
            # 评分
            if count >= 5:
                total_score += 100000
            elif count == 4:
                if open_ends == 2:
                    total_score += 50000  # 活四
                elif open_ends == 1:
                    total_score += 5000   # 冲四
            elif count == 3:
                if open_ends == 2:
                    total_score += 3000   # 活三
                elif open_ends == 1:
                    total_score += 300    # 眠三
            elif count == 2:
                if open_ends == 2:
                    total_score += 100    # 活二
                elif open_ends == 1:
                    total_score += 10     # 眠二
        
        return total_score
    
    def _evaluate_board(self, board, size, my_color, opponent):
        """评估整个棋盘"""
        my_score = 0
        opp_score = 0
        
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        checked = set()
        
        for i in range(size):
            for j in range(size):
                stone = board.grid[i][j]
                if not stone:
                    continue
                
                for idx, (dr, dc) in enumerate(directions):
                    key = (i, j, idx)
                    if key in checked:
                        continue
                    
                    # 计算这条线
                    count = 1
                    open_ends = 0
                    positions = [(i, j)]
                    
                    r, c = i + dr, j + dc
                    while 0 <= r < size and 0 <= c < size and board.grid[r][c] == stone:
                        count += 1
                        positions.append((r, c))
                        r, c = r + dr, c + dc
                    if 0 <= r < size and 0 <= c < size and board.grid[r][c] is None:
                        open_ends += 1
                    
                    r, c = i - dr, j - dc
                    while 0 <= r < size and 0 <= c < size and board.grid[r][c] == stone:
                        count += 1
                        positions.append((r, c))
                        r, c = r - dr, c - dc
                    if 0 <= r < size and 0 <= c < size and board.grid[r][c] is None:
                        open_ends += 1
                    
                    # 标记已检查
                    for pos in positions:
                        checked.add((pos[0], pos[1], idx))
                    
                    # 计分
                    line_score = 0
                    if count >= 5:
                        line_score = 100000
                    elif count == 4:
                        line_score = 50000 if open_ends == 2 else 5000
                    elif count == 3:
                        line_score = 3000 if open_ends == 2 else 300
                    elif count == 2:
                        line_score = 100 if open_ends == 2 else 10
                    
                    if stone == my_color:
                        my_score += line_score
                    else:
                        opp_score += line_score
        
        return my_score - opp_score * 1.1
    
    # ========== 黑白棋部分 ==========
    
    def _get_othello_move(self, game, color):
        """黑白棋走法"""
        valid_moves = game.get_valid_moves()
        if not valid_moves:
            return None
        
        weights = [
            [100, -20, 10, 5, 5, 10, -20, 100],
            [-20, -50, -2, -2, -2, -2, -50, -20],
            [10, -2, 1, 1, 1, 1, -2, 10],
            [5, -2, 1, 0, 0, 1, -2, 5],
            [5, -2, 1, 0, 0, 1, -2, 5],
            [10, -2, 1, 1, 1, 1, -2, 10],
            [-20, -50, -2, -2, -2, -2, -50, -20],
            [100, -20, 10, 5, 5, 10, -20, 100],
        ]
        
        best_score = float('-inf')
        best_move = valid_moves[0]
        
        for move in valid_moves:
            score = weights[move[0]][move[1]]
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move