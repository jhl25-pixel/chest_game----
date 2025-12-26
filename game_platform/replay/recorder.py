# game_platform/replay/recorder.py
"""
游戏录像记录器
设计模式：观察者模式
"""

import json
import time
import copy


class GameRecorder:
    """游戏录像记录器"""
    
    def __init__(self):
        self.recording = False
        self.records = []
        self.metadata = {}
        self.initial_state = None
    
    def start_recording(self, game, black_player=None, white_player=None):
        """开始录像
        
        Args:
            game: 游戏实例
            black_player: 黑方玩家信息
            white_player: 白方玩家信息
        """
        self.recording = True
        self.records = []
        
        # 记录元数据
        self.metadata = {
            'game_type': game.get_game_type(),
            'board_size': game.board_size,
            'start_time': time.time(),
            'black_player': self._get_player_info(black_player),
            'white_player': self._get_player_info(white_player),
        }
        
        # 记录初始棋盘状态
        self.initial_state = self._capture_board_state(game)
    
    def _get_player_info(self, player):
        """获取玩家信息"""
        if player is None:
            return {'name': '游客', 'type': 'guest'}
        
        info = {
            'name': player.name,
            'type': 'ai' if not player.is_human() else 'human'
        }
        
        if not player.is_human():
            info['ai_level'] = player.level
        
        if player.user:
            info['username'] = player.user.username
            info['stats'] = {
                'games': player.user.games,
                'wins': player.user.wins
            }
        
        return info
    
    def _capture_board_state(self, game):
        """捕获棋盘状态"""
        return [[game.board.grid[i][j] for j in range(game.board_size)] 
                for i in range(game.board_size)]
    
    def record_move(self, game, move_data):
        """记录一步棋
        
        Args:
            game: 游戏实例
            move_data: 落子数据
        """
        if not self.recording:
            return
        
        record = {
            'move_number': len(self.records) + 1,
            'timestamp': time.time(),
            'player': move_data.get('player'),
            'type': move_data.get('type', 'move'),
            'row': move_data.get('row'),
            'col': move_data.get('col'),
            'board_after': self._capture_board_state(game),
        }
        
        # 黑白棋特有：记录翻转的棋子
        if 'flipped' in move_data:
            record['flipped'] = move_data['flipped']
        
        # 围棋特有：记录被提的棋子
        if 'captured' in move_data:
            record['captured'] = move_data['captured']
        
        self.records.append(record)
    
    def stop_recording(self, game):
        """停止录像
        
        Args:
            game: 游戏实例
            
        Returns:
            dict: 完整的录像数据
        """
        self.recording = False
        
        self.metadata['end_time'] = time.time()
        self.metadata['winner'] = game.winner
        self.metadata['game_over'] = game.game_over
        self.metadata['total_moves'] = len(self.records)
        
        if hasattr(game, 'final_score'):
            self.metadata['final_score'] = game.final_score.copy()
        
        return self.get_replay_data()
    
    def get_replay_data(self):
        """获取录像数据"""
        return {
            'metadata': copy.deepcopy(self.metadata),
            'initial_state': copy.deepcopy(self.initial_state),
            'records': copy.deepcopy(self.records)
        }
    
    def save_to_file(self, filename):
        """保存录像到文件
        
        Args:
            filename: 文件名
        """
        data = self.get_replay_data()
        
        if not filename.endswith('.replay'):
            filename += '.replay'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    @staticmethod
    def load_from_file(filename):
        """从文件加载录像
        
        Args:
            filename: 文件名
            
        Returns:
            dict: 录像数据
        """
        if not filename.endswith('.replay'):
            filename += '.replay'
        
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)