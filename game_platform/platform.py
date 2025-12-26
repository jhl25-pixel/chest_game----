# game_platform/platform.py
"""
游戏平台后端
设计模式：外观模式、观察者模式
"""

import json
from game_platform.game import GomokuGame, GoGame, OthelloGame
from game_platform.player import PlayerFactory, HumanPlayer, AIPlayer
from game_platform.user import UserManager
from game_platform.replay import GameRecorder, GameReplayer


class GamePlatform:
    """游戏平台"""
    
    GAME_CLASSES = {
        'gomoku': GomokuGame,
        'go': GoGame,
        'othello': OthelloGame
    }
    
    def __init__(self):
        self.current_game = None
        self.max_undo_count = 5
        self.undo_count = 0
        
        # 玩家管理
        self.black_player = None
        self.white_player = None
        
        # 用户管理
        self.user_manager = UserManager()
        
        # 录像功能
        self.recorder = GameRecorder()
        self.replayer = GameReplayer()
        self.is_recording = False
        self.replay_mode = False
        
    def create_game(self, game_type, board_size, 
                    black_player_type='human', white_player_type='human',
                    black_ai_level=1, white_ai_level=1,
                    black_user=None, white_user=None):
        """创建游戏
        
        Args:
            game_type: 游戏类型 ('gomoku', 'go', 'othello')
            board_size: 棋盘大小 (8-19)
            black_player_type: 黑方类型 ('human' 或 'ai')
            white_player_type: 白方类型 ('human' 或 'ai')
            black_ai_level: 黑方AI等级 (1-3)
            white_ai_level: 白方AI等级 (1-3)
            black_user: 黑方用户账户
            white_user: 白方用户账户
        """
        if not (8 <= board_size <= 19):
            raise ValueError("棋盘大小必须在8到19之间")
        
        if game_type not in self.GAME_CLASSES:
            raise ValueError("不支持的游戏类型")
        
        self.current_game = self.GAME_CLASSES[game_type](board_size)
        
        self._create_players(game_type, black_player_type, white_player_type,
                            black_ai_level, white_ai_level, black_user, white_user)
        
        self.undo_count = 0
        self.replay_mode = False
        
        self.recorder.start_recording(self.current_game, 
                                      self.black_player, self.white_player)
        self.is_recording = True
        
        # 如果黑方是AI，自动落子
        if not self.black_player.is_human():
            self._ai_move()
    
    def _create_players(self, game_type, black_type, white_type,
                       black_ai_level, white_ai_level, black_user, white_user):
        """创建玩家"""
        if black_type == 'ai':
            self.black_player = PlayerFactory.create_ai_player('black', black_ai_level, game_type)
        else:
            self.black_player = PlayerFactory.create_human_player('black', black_user)
        
        if white_type == 'ai':
            self.white_player = PlayerFactory.create_ai_player('white', white_ai_level, game_type)
        else:
            self.white_player = PlayerFactory.create_human_player('white', white_user)
    
    def get_current_player(self):
        """获取当前玩家"""
        if not self.current_game:
            return None
        
        if self.current_game.current_player == 'black':
            return self.black_player
        return self.white_player
    
    def make_move(self, row, col):
        """落子"""
        if self.current_game is None:
            raise ValueError("请先开始游戏")
        
        if self.replay_mode:
            raise ValueError("回放模式下不能落子")
        
        current_player = self.get_current_player()
        
        if current_player and current_player.is_human():
            current_player.set_move(row, col)
        
        self.current_game.make_move(row, col)
        
        if self.is_recording and self.current_game.move_history:
            self.recorder.record_move(self.current_game, 
                                     self.current_game.move_history[-1])
        
        self.undo_count = 0
        
        if self.current_game.game_over:
            self._on_game_over()
        else:
            self._ai_move()
    
    def _ai_move(self):
        """AI自动落子"""
        while not self.current_game.game_over:
            current_player = self.get_current_player()
            
            if current_player is None or current_player.is_human():
                break
            
            move = current_player.get_move(self.current_game)
            
            if move is None:
                # 没有合法落子，尝试弃权
                if hasattr(self.current_game, 'pass_move'):
                    try:
                        self.current_game.pass_move()
                        if self.is_recording and self.current_game.move_history:
                            self.recorder.record_move(self.current_game,
                                                     self.current_game.move_history[-1])
                    except ValueError:
                        break
                else:
                    break
            else:
                try:
                    self.current_game.make_move(move[0], move[1])
                    if self.is_recording and self.current_game.move_history:
                        self.recorder.record_move(self.current_game,
                                                 self.current_game.move_history[-1])
                except ValueError:
                    break
        
        if self.current_game.game_over:
            self._on_game_over()
    
    def pass_move(self):
        """虚着/弃权"""
        if self.current_game is None:
            raise ValueError("请先开始游戏")
        
        if self.replay_mode:
            raise ValueError("回放模式下不能操作")
        
        if not isinstance(self.current_game, (GoGame, OthelloGame)):
            raise ValueError("只有围棋和黑白棋支持弃权")
        
        self.current_game.pass_move()
        
        if self.is_recording and self.current_game.move_history:
            self.recorder.record_move(self.current_game,
                                     self.current_game.move_history[-1])
        
        self.undo_count = 0
        
        if self.current_game.game_over:
            self._on_game_over()
        else:
            self._ai_move()
    
    def _on_game_over(self):
        """游戏结束处理"""
        if self.is_recording:
            self.recorder.stop_recording(self.current_game)
            self.is_recording = False
        
        winner = self.current_game.winner
        
        # 更新用户战绩
        if winner and winner != 'draw':
            if self.black_player and self.black_player.user:
                self.user_manager.update_user_stats(
                    self.black_player.user.username,
                    winner == 'black'
                )
            
            if self.white_player and self.white_player.user:
                self.user_manager.update_user_stats(
                    self.white_player.user.username,
                    winner == 'white'
                )
    
    def undo_move(self):
        """悔棋"""
        if self.current_game is None:
            raise ValueError("请先开始游戏")
        
        if self.replay_mode:
            raise ValueError("回放模式下不能悔棋")
        
        if self.undo_count >= self.max_undo_count:
            raise ValueError(f"悔棋次数已达上限（{self.max_undo_count}次）")
        
        self.current_game.undo_move()
        self.undo_count += 1
        
    def resign(self):
        """认输"""
        if self.current_game is None:
            raise ValueError("请先开始游戏")
        
        if self.replay_mode:
            raise ValueError("回放模式下不能认输")
        
        self.current_game.resign()
        self._on_game_over()
        
    def reset_game(self, board_size=None):
        """重新开始游戏"""
        if self.current_game is None:
            raise ValueError("请先开始游戏")
        
        if board_size is not None and not (8 <= board_size <= 19):
            raise ValueError("棋盘大小必须在8到19之间")
        
        self.current_game.reset(board_size)
        self.undo_count = 0
        self.replay_mode = False
        
        self.recorder.start_recording(self.current_game,
                                      self.black_player, self.white_player)
        self.is_recording = True
        
        if self.black_player and not self.black_player.is_human():
            self._ai_move()
    
    def save_to_file(self, filename):
        """保存游戏到文件"""
        if self.current_game is None:
            raise ValueError("没有正在进行的游戏")
        
        try:
            game_state = self.current_game.save_game()
            game_state['undo_count'] = self.undo_count
            game_state['black_player'] = self._serialize_player(self.black_player)
            game_state['white_player'] = self._serialize_player(self.white_player)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(game_state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ValueError(f"保存失败: {str(e)}")
    
    def _serialize_player(self, player):
        """序列化玩家信息"""
        if player is None:
            return None
        
        data = {
            'color': player.color,
            'name': player.name,
            'is_human': player.is_human()
        }
        
        if not player.is_human():
            data['ai_level'] = player.level
        
        if player.user:
            data['username'] = player.user.username
        
        return data
    
    def load_from_file(self, filename):
        """从文件加载游戏"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                game_state = json.load(f)
            
            game_type = game_state.get('type')
            board_size = game_state.get('board_size')
            
            if game_type not in self.GAME_CLASSES:
                raise ValueError("不支持的游戏类型")
            
            self.current_game = self.GAME_CLASSES[game_type](board_size)
            self.current_game.load_game(game_state)
            
            self._deserialize_players(game_state, game_type)
            
            self.undo_count = game_state.get('undo_count', 0)
            self.replay_mode = False
            
        except FileNotFoundError:
            raise ValueError("文件不存在")
        except json.JSONDecodeError:
            raise ValueError("文件格式错误")
        except Exception as e:
            raise ValueError(f"加载失败: {str(e)}")
    
    def _deserialize_players(self, game_state, game_type):
        """反序列化玩家信息"""
        black_data = game_state.get('black_player', {})
        white_data = game_state.get('white_player', {})
        
        if not black_data or black_data.get('is_human', True):
            username = black_data.get('username') if black_data else None
            user = self.user_manager.get_user(username) if username else None
            self.black_player = PlayerFactory.create_human_player('black', user)
        else:
            level = black_data.get('ai_level', 1)
            self.black_player = PlayerFactory.create_ai_player('black', level, game_type)
        
        if not white_data or white_data.get('is_human', True):
            username = white_data.get('username') if white_data else None
            user = self.user_manager.get_user(username) if username else None
            self.white_player = PlayerFactory.create_human_player('white', user)
        else:
            level = white_data.get('ai_level', 1)
            self.white_player = PlayerFactory.create_ai_player('white', level, game_type)
    
    def save_replay(self, filename):
        """保存录像"""
        if not self.recorder.records and not self.current_game:
            raise ValueError("没有可保存的录像")
        
        filename = self.recorder.save_to_file(filename)
        
        if self.black_player and self.black_player.user:
            self.user_manager.add_user_replay(
                self.black_player.user.username, filename)
        if self.white_player and self.white_player.user:
            self.user_manager.add_user_replay(
                self.white_player.user.username, filename)
        
        return filename
    
    def load_replay(self, filename):
        """加载录像进入回放模式"""
        self.replayer.load_replay(filename)
        self.current_game = self.replayer.game
        self.replay_mode = True
        self.is_recording = False
    
    def replay_next(self):
        """回放下一步"""
        if not self.replay_mode:
            raise ValueError("不在回放模式")
        return self.replayer.next_step()
    
    def replay_prev(self):
        """回放上一步"""
        if not self.replay_mode:
            raise ValueError("不在回放模式")
        return self.replayer.prev_step()
    
    def replay_goto(self, step):
        """回放跳转到指定步"""
        if not self.replay_mode:
            raise ValueError("不在回放模式")
        self.replayer.goto_step(step)
    
    def replay_reset(self):
        """回放重置"""
        if not self.replay_mode:
            raise ValueError("不在回放模式")
        self.replayer.reset()
    
    def exit_replay(self):
        """退出回放模式"""
        self.replay_mode = False
        self.current_game = None
    
    def get_game_state(self):
        """获取游戏状态"""
        if self.current_game is None:
            return None
        
        state = {
            'board': self.current_game.board,
            'current_player': self.current_game.current_player,
            'game_over': self.current_game.game_over,
            'winner': self.current_game.winner,
            'undo_count': self.undo_count,
            'max_undo_count': self.max_undo_count,
            'black_player': self.black_player,
            'white_player': self.white_player,
            'replay_mode': self.replay_mode
        }
        
        if self.replay_mode:
            state['replay_step'] = self.replayer.get_current_step()
            state['replay_total'] = self.replayer.get_total_steps()
            state['replay_metadata'] = self.replayer.get_metadata()
        
        if hasattr(self.current_game, 'final_score'):
            state['final_score'] = self.current_game.final_score
        
        return state
    
    def register_user(self, username, password):
        """注册用户"""
        return self.user_manager.register(username, password)
    
    def login_user(self, username, password):
        """用户登录"""
        return self.user_manager.login(username, password)
    
    def get_leaderboard(self, limit=10):
        """获取排行榜"""
        return self.user_manager.get_leaderboard(limit)