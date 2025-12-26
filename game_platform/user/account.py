# game_platform/user/account.py
"""
用户账户类
"""

import hashlib
import time


class User:
    """用户账户"""
    
    def __init__(self, username, password_hash=None):
        self.username = username
        self.password_hash = password_hash
        self.games = 0  # 总对战场次
        self.wins = 0   # 胜场
        self.created_at = time.time()
        self.last_login = None
        self.replays = []  # 关联的录像文件列表
    
    @staticmethod
    def hash_password(password):
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password):
        """验证密码"""
        return self.password_hash == self.hash_password(password)
    
    def update_stats(self, won):
        """更新战绩
        
        Args:
            won: 是否获胜
        """
        self.games += 1
        if won:
            self.wins += 1
    
    def get_win_rate(self):
        """获取胜率"""
        if self.games == 0:
            return 0.0
        return self.wins / self.games
    
    def add_replay(self, replay_filename):
        """添加录像文件"""
        if replay_filename not in self.replays:
            self.replays.append(replay_filename)
    
    def remove_replay(self, replay_filename):
        """移除录像文件"""
        if replay_filename in self.replays:
            self.replays.remove(replay_filename)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'username': self.username,
            'password_hash': self.password_hash,
            'games': self.games,
            'wins': self.wins,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'replays': self.replays.copy()
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建用户"""
        user = cls(data['username'], data['password_hash'])
        user.games = data.get('games', 0)
        user.wins = data.get('wins', 0)
        user.created_at = data.get('created_at', time.time())
        user.last_login = data.get('last_login')
        user.replays = data.get('replays', [])
        return user
    
    def __str__(self):
        return f"{self.username} ({self.wins}胜/{self.games}场)"