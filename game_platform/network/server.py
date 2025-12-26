# game_platform/network/server.py
"""
网络对战服务器（修复版v2）
"""
import socket
import threading
import json
from game_platform.board import GomokuBoard, GoBoard, OthelloBoard


class GameServer:
    """游戏服务器"""
    
    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # {socket: {'username': str, 'color': str, 'buffer': str}}
        self.running = False
        self.lock = threading.Lock()
        
        # 游戏状态
        self.game_type = None
        self.board_size = 15
        self.board = None
        self.current_player = 'black'
        self.game_started = False
        self.game_over = False
        self.winner = None
        
        # 回调
        self.on_log = None
        
    def log(self, msg):
        """输出日志"""
        print(f"[Server] {msg}")
        if self.on_log:
            try:
                self.on_log(msg)
            except:
                pass
    
    def start(self):
        """启动服务器"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(2)
        self.running = True
        
        self.log(f"服务器启动在 {self.host}:{self.port}")
        
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                try:
                    client_socket, addr = self.server_socket.accept()
                    self.log(f"新连接: {addr}")
                    
                    # 初始化客户端数据（在启动线程之前！）
                    with self.lock:
                        self.clients[client_socket] = {
                            'username': None,
                            'color': None,
                            'buffer': '',
                            'addr': addr
                        }
                    
                    # 启动客户端处理线程
                    thread = threading.Thread(target=self._handle_client, args=(client_socket, addr))
                    thread.daemon = True
                    thread.start()
                    
                except socket.timeout:
                    continue
            except Exception as e:
                if self.running:
                    self.log(f"接受连接错误: {e}")
                break
        
        self.log("服务器已停止")
    
    def stop(self):
        """停止服务器"""
        self.running = False
        
        with self.lock:
            for client_socket in list(self.clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
            self.clients.clear()
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
    
    def _handle_client(self, client_socket, addr):
        """处理客户端连接"""
        self.log(f"开始处理客户端 {addr}")
        
        try:
            # 短超时，便于检测断开
            client_socket.settimeout(1.0)
            
            while self.running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        self.log(f"客户端 {addr} 关闭连接")
                        break
                    
                    decoded = data.decode('utf-8')
                    self.log(f"收到数据 from {addr}: {decoded[:100]}")
                    
                    # 获取并更新缓冲区
                    with self.lock:
                        if client_socket not in self.clients:
                            self.log(f"客户端 {addr} 不在列表中")
                            break
                        self.clients[client_socket]['buffer'] += decoded
                        buffer = self.clients[client_socket]['buffer']
                    
                    # 处理完整消息
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        
                        with self.lock:
                            if client_socket in self.clients:
                                self.clients[client_socket]['buffer'] = buffer
                        
                        if line.strip():
                            self._process_message(client_socket, line.strip())
                            
                except socket.timeout:
                    continue
                except Exception as e:
                    self.log(f"接收错误 from {addr}: {e}")
                    break
                    
        except Exception as e:
            self.log(f"处理客户端 {addr} 出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._remove_client(client_socket)
    
    def _process_message(self, client_socket, data):
        """处理消息"""
        try:
            msg = json.loads(data)
            msg_type = msg.get('type')
            
            self.log(f"收到消息类型: {msg_type}")
            
            if msg_type == 'join':
                self._handle_join(client_socket, msg)
            elif msg_type == 'create_game':
                self._handle_create_game(client_socket, msg)
            elif msg_type == 'move':
                self._handle_move(client_socket, msg)
            elif msg_type == 'pass':
                self._handle_pass(client_socket, msg)
            elif msg_type == 'resign':
                self._handle_resign(client_socket, msg)
            elif msg_type == 'undo_request':
                self._handle_undo_request(client_socket, msg)
            elif msg_type == 'undo_response':
                self._handle_undo_response(client_socket, msg)
            else:
                self.log(f"未知消息类型: {msg_type}")
                
        except json.JSONDecodeError as e:
            self.log(f"JSON解析错误: {e}")
        except Exception as e:
            self.log(f"处理消息出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _handle_join(self, client_socket, msg):
        """处理加入请求"""
        username = msg.get('username', 'Player')
        preferred_color = msg.get('color', 'black')
        
        self.log(f"处理 join: {username}, 偏好颜色: {preferred_color}")
        
        assigned_color = None
        
        with self.lock:
            # 检查已占用的颜色
            taken_colors = set()
            for sock, info in self.clients.items():
                if info.get('color'):
                    taken_colors.add(info['color'])
            
            self.log(f"已占用颜色: {taken_colors}")
            
            # 分配颜色
            if preferred_color not in taken_colors:
                assigned_color = preferred_color
            elif 'black' not in taken_colors:
                assigned_color = 'black'
            elif 'white' not in taken_colors:
                assigned_color = 'white'
            else:
                self.log(f"房间已满，拒绝 {username}")
                self._send_to_client(client_socket, {
                    'type': 'error',
                    'message': '房间已满'
                })
                return
            
            # 更新客户端信息
            if client_socket in self.clients:
                self.clients[client_socket]['username'] = username
                self.clients[client_socket]['color'] = assigned_color
                self.log(f"玩家 {username} 加入，分配颜色: {assigned_color}")
            else:
                self.log(f"错误: client_socket 不在 clients 中")
                return
        
        # 发送颜色分配（在锁外）
        self.log(f"发送 color_assigned 给 {username}: {assigned_color}")
        self._send_to_client(client_socket, {
            'type': 'color_assigned',
            'color': assigned_color,
            'username': username
        })
        
        # 广播玩家列表
        self._broadcast_players()
    
    def _handle_create_game(self, client_socket, msg):
        """处理创建游戏"""
        self.game_type = msg.get('game_type', 'gomoku')
        self.board_size = msg.get('board_size', 15)
        
        # 创建棋盘
        if self.game_type == 'gomoku':
            self.board = GomokuBoard(self.board_size)
        elif self.game_type == 'go':
            self.board = GoBoard(self.board_size)
        elif self.game_type == 'othello':
            self.board = OthelloBoard(self.board_size)
            mid = self.board_size // 2
            self.board.grid[mid-1][mid-1] = 'white'
            self.board.grid[mid-1][mid] = 'black'
            self.board.grid[mid][mid-1] = 'black'
            self.board.grid[mid][mid] = 'white'
        else:
            self.board = GomokuBoard(self.board_size)
        
        self.current_player = 'black'
        self.game_started = True
        self.game_over = False
        self.winner = None
        
        self.log(f"游戏已创建: {self.game_type} {self.board_size}x{self.board_size}")
        
        self._broadcast({
            'type': 'game_start',
            'game_type': self.game_type,
            'board_size': self.board_size
        })
        
        self._broadcast_state()
    
    def _handle_move(self, client_socket, msg):
        """处理落子"""
        if not self.game_started or self.game_over:
            return
        
        row = msg.get('row')
        col = msg.get('col')
        
        with self.lock:
            client_info = self.clients.get(client_socket, {})
            client_color = client_info.get('color')
            
            if client_color != self.current_player:
                self._send_to_client(client_socket, {
                    'type': 'error',
                    'message': '不是你的回合'
                })
                return
            
            if row is None or col is None:
                return
            if not (0 <= row < self.board_size and 0 <= col < self.board_size):
                return
            if self.board.grid[row][col] is not None:
                self._send_to_client(client_socket, {
                    'type': 'error',
                    'message': '该位置已有棋子'
                })
                return
            
            self.board.grid[row][col] = self.current_player
            
            if self.game_type == 'othello':
                self._flip_stones(row, col, self.current_player)
            
            self.log(f"{self.current_player} 落子: ({row}, {col})")
            
            if self._check_winner():
                self.game_over = True
                self.log(f"游戏结束，胜者: {self.winner}")
        
        if self.game_over:
            self._broadcast({
                'type': 'game_over',
                'winner': self.winner
            })
        else:
            self.current_player = 'white' if self.current_player == 'black' else 'black'
        
        self._broadcast_state()
    
    def _handle_pass(self, client_socket, msg):
        """处理弃权"""
        if not self.game_started or self.game_over:
            return
        
        with self.lock:
            client_info = self.clients.get(client_socket, {})
            if client_info.get('color') != self.current_player:
                return
            
            self.log(f"{self.current_player} 弃权")
            self.current_player = 'white' if self.current_player == 'black' else 'black'
        
        self._broadcast_state()
    
    def _handle_resign(self, client_socket, msg):
        """处理认输"""
        if not self.game_started or self.game_over:
            return
        
        with self.lock:
            client_info = self.clients.get(client_socket, {})
            loser_color = client_info.get('color')
            
            if not loser_color:
                return
            
            self.game_over = True
            self.winner = 'white' if loser_color == 'black' else 'black'
            self.log(f"{loser_color} 认输，{self.winner} 获胜")
        
        self._broadcast({
            'type': 'game_over',
            'winner': self.winner
        })
    
    def _handle_undo_request(self, client_socket, msg):
        """处理悔棋请求"""
        with self.lock:
            client_info = self.clients.get(client_socket, {})
            from_user = client_info.get('username', '对方')
            
            for sock, info in self.clients.items():
                if sock != client_socket:
                    self._send_to_client(sock, {
                        'type': 'undo_request',
                        'from': from_user
                    })
    
    def _handle_undo_response(self, client_socket, msg):
        """处理悔棋响应"""
        accepted = msg.get('accepted', False)
        
        self._broadcast({
            'type': 'message',
            'message': '悔棋已同意' if accepted else '悔棋被拒绝'
        })
    
    def _flip_stones(self, row, col, color):
        """黑白棋翻转"""
        opponent = 'white' if color == 'black' else 'black'
        directions = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        
        for dr, dc in directions:
            to_flip = []
            r, c = row + dr, col + dc
            
            while 0 <= r < self.board_size and 0 <= c < self.board_size:
                if self.board.grid[r][c] == opponent:
                    to_flip.append((r, c))
                    r, c = r + dr, c + dc
                elif self.board.grid[r][c] == color:
                    for fr, fc in to_flip:
                        self.board.grid[fr][fc] = color
                    break
                else:
                    break
    
    def _check_winner(self):
        """检查胜负"""
        if self.game_type == 'gomoku':
            return self._check_gomoku_winner()
        elif self.game_type == 'othello':
            return self._check_othello_winner()
        return False
    
    def _check_gomoku_winner(self):
        """五子棋胜负"""
        directions = [(0,1),(1,0),(1,1),(1,-1)]
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                stone = self.board.grid[i][j]
                if not stone:
                    continue
                
                for dr, dc in directions:
                    count = 1
                    r, c = i + dr, j + dc
                    while 0 <= r < self.board_size and 0 <= c < self.board_size:
                        if self.board.grid[r][c] == stone:
                            count += 1
                            r, c = r + dr, c + dc
                        else:
                            break
                    
                    if count >= 5:
                        self.winner = stone
                        return True
        return False
    
    def _check_othello_winner(self):
        """黑白棋胜负"""
        empty = black = white = 0
        
        for i in range(self.board_size):
            for j in range(self.board_size):
                stone = self.board.grid[i][j]
                if stone is None:
                    empty += 1
                elif stone == 'black':
                    black += 1
                else:
                    white += 1
        
        if empty == 0:
            if black > white:
                self.winner = 'black'
            elif white > black:
                self.winner = 'white'
            else:
                self.winner = 'draw'
            return True
        return False
    
    def _broadcast_players(self):
        """广播玩家列表"""
        players = {}
        with self.lock:
            for info in self.clients.values():
                color = info.get('color')
                username = info.get('username')
                if color and username:
                    players[color] = username
        
        self.log(f"广播玩家: {players}")
        
        self._broadcast({
            'type': 'players_update',
            'players': players
        })
    
    def _broadcast_state(self):
        """广播游戏状态"""
        if not self.board:
            return
        
        board_data = [[self.board.grid[i][j] for j in range(self.board_size)] 
                      for i in range(self.board_size)]
        
        players = {}
        with self.lock:
            for info in self.clients.values():
                color = info.get('color')
                username = info.get('username')
                if color and username:
                    players[color] = username
        
        self._broadcast({
            'type': 'state_update',
            'board': board_data,
            'board_size': self.board_size,
            'current_player': self.current_player,
            'game_over': self.game_over,
            'winner': self.winner,
            'game_type': self.game_type,
            'players': players
        })
    
    def _broadcast(self, msg):
        """广播"""
        with self.lock:
            sockets = list(self.clients.keys())
        
        for sock in sockets:
            self._send_to_client(sock, msg)
    
    def _send_to_client(self, client_socket, msg):
        """发送消息"""
        try:
            data = json.dumps(msg) + '\n'
            client_socket.sendall(data.encode('utf-8'))
        except Exception as e:
            self.log(f"发送失败: {e}")
    
    def _remove_client(self, client_socket):
        """移除客户端"""
        with self.lock:
            if client_socket in self.clients:
                info = self.clients[client_socket]
                self.log(f"移除玩家: {info.get('username')}")
                del self.clients[client_socket]
        
        try:
            client_socket.close()
        except:
            pass
        
        self._broadcast_players()