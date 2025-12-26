# game_platform/user/manager.py
"""
用户管理器
设计模式：单例模式
"""

import json
import os
import time
from game_platform.user.account import User


class UserManager:
    """用户管理器（单例）"""
    
    _instance = None
    DEFAULT_FILE = 'users.json'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.users = {}  # username -> User
        self.data_file = self.DEFAULT_FILE
        self._load_users()
        self._initialized = True
    
    def _load_users(self):
        """从文件加载用户数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        self.users[username] = User.from_dict(user_data)
            except (json.JSONDecodeError, KeyError):
                self.users = {}
    
    def _save_users(self):
        """保存用户数据到文件"""
        data = {username: user.to_dict() for username, user in self.users.items()}
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def register(self, username, password):
        """注册新用户
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            User: 新创建的用户
            
        Raises:
            ValueError: 用户名已存在或无效
        """
        if not username or not password:
            raise ValueError("用户名和密码不能为空")
        
        if len(username) < 2 or len(username) > 20:
            raise ValueError("用户名长度必须在2-20个字符之间")
        
        if len(password) < 4:
            raise ValueError("密码长度至少4个字符")
        
        if username in self.users:
            raise ValueError("用户名已存在")
        
        password_hash = User.hash_password(password)
        user = User(username, password_hash)
        user.last_login = time.time()
        
        self.users[username] = user
        self._save_users()
        
        return user
    
    def login(self, username, password):
        """用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            User: 登录的用户
            
        Raises:
            ValueError: 用户名或密码错误
        """
        if username not in self.users:
            raise ValueError("用户名或密码错误")
        
        user = self.users[username]
        if not user.verify_password(password):
            raise ValueError("用户名或密码错误")
        
        user.last_login = time.time()
        self._save_users()
        
        return user
    
    def get_user(self, username):
        """获取用户"""
        return self.users.get(username)
    
    def update_user_stats(self, username, won):
        """更新用户战绩"""
        if username in self.users:
            self.users[username].update_stats(won)
            self._save_users()
    
    def add_user_replay(self, username, replay_filename):
        """为用户添加录像"""
        if username in self.users:
            self.users[username].add_replay(replay_filename)
            self._save_users()
    
    def get_leaderboard(self, limit=10):
        """获取排行榜
        
        Args:
            limit: 返回数量
            
        Returns:
            list: 按胜场排序的用户列表
        """
        sorted_users = sorted(
            self.users.values(),
            key=lambda u: (u.wins, u.get_win_rate()),
            reverse=True
        )
        return sorted_users[:limit]
    
    def get_all_users(self):
        """获取所有用户"""
        return list(self.users.values())