# game_platform/replay/replayer.py
"""
游戏回放器
"""

import time
from game_platform.game import GomokuGame, GoGame, OthelloGame
from game_platform.replay.recorder import GameRecorder


class GameReplayer:
    """游戏回放器"""
    
    def __init__(self):
        self.replay_data = None
        self.current_step = 0
        self.game = None
        self.is_playing = False
        self.playback_speed = 1.0  # 回放速度
    
    def load_replay(self, filename):
        """加载录像文件
        
        Args:
            filename: 录像文件名
        """
        self.replay_data = GameRecorder.load_from_file(filename)
        self.current_step = 0
        self._create_game()
    
    def load_replay_data(self, replay_data):
        """加载录像数据
        
        Args:
            replay_data: 录像数据字典
        """
        self.replay_data = replay_data
        self.current_step = 0
        self._create_game()
    
    def _create_game(self):
        """根据录像创建游戏实例"""
        if not self.replay_data:
            return
        
        metadata = self.replay_data['metadata']
        game_type = metadata['game_type']
        board_size = metadata['board_size']
        
        if game_type == 'gomoku':
            self.game = GomokuGame(board_size)
        elif game_type == 'go':
            self.game = GoGame(board_size)
        elif game_type == 'othello':
            self.game = OthelloGame(board_size)
        else:
            raise ValueError(f"不支持的游戏类型: {game_type}")
        
        # 恢复初始状态
        initial_state = self.replay_data['initial_state']
        for i in range(board_size):
            for j in range(board_size):
                self.game.board.grid[i][j] = initial_state[i][j]
    
    def get_metadata(self):
        """获取录像元数据"""
        if self.replay_data:
            return self.replay_data['metadata']
        return None
    
    def get_total_steps(self):
        """获取总步数"""
        if self.replay_data:
            return len(self.replay_data['records'])
        return 0
    
    def get_current_step(self):
        """获取当前步数"""
        return self.current_step
    
    def next_step(self):
        """前进一步
        
        Returns:
            dict: 当前步骤的信息，如果已到末尾返回None
        """
        if not self.replay_data:
            return None
        
        records = self.replay_data['records']
        
        if self.current_step >= len(records):
            return None
        
        record = records[self.current_step]
        
        # 更新棋盘状态
        board_after = record['board_after']
        for i in range(len(board_after)):
            for j in range(len(board_after[i])):
                self.game.board.grid[i][j] = board_after[i][j]
        
        # 更新当前玩家
        if self.current_step + 1 < len(records):
            next_record = records[self.current_step + 1]
            self.game.current_player = next_record['player']
        
        self.current_step += 1
        return record
    
    def prev_step(self):
        """后退一步
        
        Returns:
            dict: 当前步骤的信息，如果已到开头返回None
        """
        if not self.replay_data:
            return None
        
        if self.current_step <= 0:
            return None
        
        self.current_step -= 1
        
        if self.current_step == 0:
            # 恢复到初始状态
            initial_state = self.replay_data['initial_state']
            for i in range(len(initial_state)):
                for j in range(len(initial_state[i])):
                    self.game.board.grid[i][j] = initial_state[i][j]
            self.game.current_player = 'black'
            return {'type': 'initial'}
        
        # 恢复到上一步的状态
        record = self.replay_data['records'][self.current_step - 1]
        board_after = record['board_after']
        for i in range(len(board_after)):
            for j in range(len(board_after[i])):
                self.game.board.grid[i][j] = board_after[i][j]
        
        return record
    
    def goto_step(self, step):
        """跳转到指定步数
        
        Args:
            step: 目标步数 (0 表示初始状态)
        """
        if not self.replay_data:
            return
        
        step = max(0, min(step, len(self.replay_data['records'])))
        
        if step == 0:
            # 恢复到初始状态
            initial_state = self.replay_data['initial_state']
            for i in range(len(initial_state)):
                for j in range(len(initial_state[i])):
                    self.game.board.grid[i][j] = initial_state[i][j]
            self.game.current_player = 'black'
        else:
            # 恢复到指定步骤
            record = self.replay_data['records'][step - 1]
            board_after = record['board_after']
            for i in range(len(board_after)):
                for j in range(len(board_after[i])):
                    self.game.board.grid[i][j] = board_after[i][j]
        
        self.current_step = step
    
    def reset(self):
        """重置到开始"""
        self.goto_step(0)
    
    def get_current_board(self):
        """获取当前棋盘"""
        if self.game:
            return self.game.board
        return None
    
    def get_step_info(self, step):
        """获取指定步骤的信息
        
        Args:
            step: 步数 (1-indexed)
            
        Returns:
            dict: 步骤信息
        """
        if not self.replay_data:
            return None
        
        if step < 1 or step > len(self.replay_data['records']):
            return None
        
        return self.replay_data['records'][step - 1]
    
    def auto_play(self, callback=None, delay=1.0):
        """自动回放
        
        Args:
            callback: 每步执行后的回调函数
            delay: 每步之间的延迟（秒）
        """
        self.is_playing = True
        
        while self.is_playing and self.current_step < self.get_total_steps():
            record = self.next_step()
            
            if callback:
                callback(record, self.current_step, self.get_total_steps())
            
            time.sleep(delay / self.playback_speed)
        
        self.is_playing = False
    
    def stop_play(self):
        """停止自动回放"""
        self.is_playing = False
    
    def set_speed(self, speed):
        """设置回放速度
        
        Args:
            speed: 速度倍率 (0.5-4.0)
        """
        self.playback_speed = max(0.5, min(4.0, speed))