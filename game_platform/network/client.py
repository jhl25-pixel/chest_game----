# game_platform/network/client.py
"""
网络对战客户端（修复版v2）
"""
import socket
import threading
import json
import time
from game_platform.board import GomokuBoard, GoBoard, OthelloBoard


class NetworkClient:
    """网络客户端"""
    
    def __init__(self):
        self.socket = None
        self.connected = False
        self.color = None
        self.username = None
        self.lock = threading.Lock()
        
        # 游戏状态
        self.board = None
        self.board_size = 15
        self.current_player = 'black'
        self.game_over = False
        self.winner = None
        self.game_type = None
        self.players = {}
        
        # 回调函数
        self.on_message = None
        self.on_state_update = None
        self.on_game_start = None
        self.on_game_over = None
        self.on_undo_request = None
        
        # 接收线程
        self._recv_thread = None
        self._running = False
    
    def connect(self, host, port, username, preferred_color='black'):
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, int(port)))
            self.connected = True
            self.username = username
            self._running = True
            
            print(f"[Client] 已连接到 {host}:{port}")
            
            # 启动接收线程
            self._recv_thread = threading.Thread(target=self._receive_loop)
            self._recv_thread.daemon = True
            self._recv_thread.start()
            
            # 等待接收线程启动
            time.sleep(0.1)
            
            # 发送加入请求
            print(f"[Client] 发送 join 请求: {username}, {preferred_color}")
            success = self._send({
                'type': 'join',
                'username': username,
                'color': preferred_color
            })
            print(f"[Client] join 请求发送结果: {success}")
            
        except Exception as e:
            print(f"[Client] 连接失败: {e}")
            self.connected = False
            raise
    
    def disconnect(self):
        """断开连接"""
        self._running = False
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        print("[Client] 已断开连接")
    
    def _receive_loop(self):
        """接收消息循环"""
        buffer = ""
        
        print("[Client] 接收线程已启动")
        
        while self._running and self.connected:
            try:
                self.socket.settimeout(1.0)
                try:
                    data = self.socket.recv(4096)
                    if not data:
                        print("[Client] 连接已关闭")
                        break
                    
                    decoded = data.decode('utf-8')
                    print(f"[Client] 收到原始数据: {decoded[:200]}")
                    buffer += decoded
                    
                    # 处理可能的多条消息
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            self._process_message(line.strip())
                            
                except socket.timeout:
                    continue
                    
            except Exception as e:
                if self._running:
                    print(f"[Client] 接收错误: {e}")
                break
        
        self.connected = False
        print("[Client] 接收线程已退出")
    
    def _process_message(self, data):
        """处理服务器消息"""
        try:
            msg = json.loads(data)
            msg_type = msg.get('type')
            
            print(f"[Client] 处理消息: {msg_type}")
            
            if msg_type == 'color_assigned':
                self._handle_color_assigned(msg)
            elif msg_type == 'players_update':
                self._handle_players_update(msg)
            elif msg_type == 'game_start':
                self._handle_game_start(msg)
            elif msg_type == 'state_update':
                self._handle_state_update(msg)
            elif msg_type == 'game_over':
                self._handle_game_over(msg)
            elif msg_type == 'undo_request':
                self._handle_undo_request(msg)
            elif msg_type == 'message':
                self._handle_message(msg)
            elif msg_type == 'error':
                self._handle_error(msg)
                
        except json.JSONDecodeError as e:
            print(f"[Client] JSON解析错误: {e}, 数据: {data[:100]}")
        except Exception as e:
            print(f"[Client] 处理消息错误: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_color_assigned(self, msg):
        """处理颜色分配"""
        self.color = msg.get('color')
        print(f"[Client] ★★★ 分配到颜色: {self.color}")
        
        if self.on_message:
            color_name = "黑方" if self.color == 'black' else "白方"
            self.on_message('info', f"你是{color_name}")
    
    def _handle_players_update(self, msg):
        """处理玩家更新"""
        self.players = msg.get('players', {})
        print(f"[Client] 玩家更新: {self.players}")
        
        # 触发状态更新以刷新界面
        if self.on_state_update and self.board:
            self.on_state_update(self.get_game_state())
    
    def _handle_game_start(self, msg):
        """处理游戏开始"""
        self.game_type = msg.get('game_type', 'gomoku')
        self.board_size = msg.get('board_size', 15)
        
        # 创建棋盘
        if self.game_type == 'gomoku':
            self.board = GomokuBoard(self.board_size)
        elif self.game_type == 'go':
            self.board = GoBoard(self.board_size)
        elif self.game_type == 'othello':
            self.board = OthelloBoard(self.board_size)
        else:
            self.board = GomokuBoard(self.board_size)
        
        self.game_over = False
        self.winner = None
        self.current_player = 'black'
        
        print(f"[Client] 游戏开始: {self.game_type} {self.board_size}x{self.board_size}")
        
        if self.on_game_start:
            self.on_game_start({
                'game_type': self.game_type,
                'board_size': self.board_size
            })
    
    def _handle_state_update(self, msg):
        """处理状态更新"""
        board_data = msg.get('board', [])
        self.board_size = msg.get('board_size', self.board_size)
        self.current_player = msg.get('current_player', 'black')
        self.game_over = msg.get('game_over', False)
        self.winner = msg.get('winner')
        self.game_type = msg.get('game_type', self.game_type)
        self.players = msg.get('players', self.players)
        
        # 更新或创建棋盘
        if self.board is None or self.board.size != self.board_size:
            if self.game_type == 'gomoku':
                self.board = GomokuBoard(self.board_size)
            elif self.game_type == 'go':
                self.board = GoBoard(self.board_size)
            elif self.game_type == 'othello':
                self.board = OthelloBoard(self.board_size)
            else:
                self.board = GomokuBoard(self.board_size)
        
        # 同步棋盘数据
        if board_data:
            for i in range(len(board_data)):
                for j in range(len(board_data[i])):
                    self.board.grid[i][j] = board_data[i][j]
        
        # 触发回调
        if self.on_state_update:
            self.on_state_update(self.get_game_state())
    
    def _handle_game_over(self, msg):
        """处理游戏结束"""
        self.game_over = True
        self.winner = msg.get('winner')
        
        print(f"[Client] 游戏结束，胜者: {self.winner}")
        
        if self.on_game_over:
            self.on_game_over({
                'winner': self.winner
            })
    
    def _handle_undo_request(self, msg):
        """处理悔棋请求"""
        if self.on_undo_request:
            self.on_undo_request(msg)
    
    def _handle_message(self, msg):
        """处理普通消息"""
        message = msg.get('message', '')
        if self.on_message:
            self.on_message('info', message)
    
    def _handle_error(self, msg):
        """处理错误消息"""
        message = msg.get('message', '未知错误')
        print(f"[Client] 错误: {message}")
        if self.on_message:
            self.on_message('error', message)
    
    def _send(self, msg):
        """发送消息"""
        if not self.connected or not self.socket:
            print("[Client] 发送失败: 未连接")
            return False
        
        try:
            data = json.dumps(msg) + '\n'
            self.socket.sendall(data.encode('utf-8'))  # 使用 sendall 确保全部发送
            print(f"[Client] 已发送: {msg.get('type')}")
            return True
        except Exception as e:
            print(f"[Client] 发送失败: {e}")
            return False
    
    def create_game(self, game_type, board_size):
        """创建游戏"""
        self._send({
            'type': 'create_game',
            'game_type': game_type,
            'board_size': board_size
        })
    
    def make_move(self, row, col):
        """落子"""
        self._send({
            'type': 'move',
            'row': row,
            'col': col
        })
    
    def pass_move(self):
        """弃权"""
        self._send({
            'type': 'pass'
        })
    
    def resign(self):
        """认输"""
        self._send({
            'type': 'resign'
        })
    
    def request_undo(self):
        """请求悔棋"""
        self._send({
            'type': 'undo_request'
        })
    
    def respond_undo(self, accepted):
        """响应悔棋请求"""
        self._send({
            'type': 'undo_response',
            'accepted': accepted
        })
    
    def get_game_state(self):
        """获取游戏状态"""
        return {
            'board': self.board,
            'board_size': self.board_size,
            'current_player': self.current_player,
            'game_over': self.game_over,
            'winner': self.winner,
            'my_color': self.color,
            'is_my_turn': self.current_player == self.color,
            'players': self.players,
            'game_type': self.game_type
        }