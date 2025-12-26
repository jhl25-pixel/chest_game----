# game_platform/ui/gui.py
"""
图形用户界面（完整版 - 支持所有功能）
"""

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, scrolledtext, ttk
from game_platform.platform import GamePlatform
from game_platform.game import GoGame, OthelloGame
import threading
from tkinter import scrolledtext

class ChessBoardCanvas(tk.Canvas):
    """棋盘画布"""
    
    def __init__(self, master, size=15, cell_size=35):
        self.board_size = size
        self.cell_size = cell_size
        self.padding = 30
        
        canvas_size = self.board_size * self.cell_size + 2 * self.padding
        super().__init__(master, width=canvas_size, height=canvas_size, bg='#DEB887')
        
        self.stones = {}
        self.last_move = None
        self.valid_move_markers = []
        self.network_mode = False
        self.network_client = None
        self.server = None
        
    def draw_board(self):
        """绘制棋盘"""
        self.delete('all')
        self.stones.clear()
        self.valid_move_markers.clear()
        
        for i in range(self.board_size):
            x1 = self.padding + i * self.cell_size
            y1 = self.padding
            x2 = x1
            y2 = self.padding + (self.board_size - 1) * self.cell_size
            self.create_line(x1, y1, x2, y2, fill='black', width=1)
            
            y1 = self.padding + i * self.cell_size
            x1 = self.padding
            y2 = y1
            x2 = self.padding + (self.board_size - 1) * self.cell_size
            self.create_line(x1, y1, x2, y2, fill='black', width=1)
        
        for i in range(self.board_size):
            x = self.padding + i * self.cell_size
            y = self.padding - 15
            self.create_text(x, y, text=chr(65 + i), font=('Arial', 10))
            
            y = self.padding + i * self.cell_size
            x = self.padding - 15
            self.create_text(x, y, text=str(i + 1), font=('Arial', 10))
        
        star_points = self._get_star_points()
        for row, col in star_points:
            x = self.padding + col * self.cell_size
            y = self.padding + row * self.cell_size
            self.create_oval(x - 3, y - 3, x + 3, y + 3, fill='black')
            
    def _get_star_points(self):
        """获取星位"""
        if self.board_size == 19:
            return [(3, 3), (3, 9), (3, 15), (9, 3), (9, 9), (9, 15), (15, 3), (15, 9), (15, 15)]
        elif self.board_size == 13:
            return [(3, 3), (3, 9), (6, 6), (9, 3), (9, 9)]
        elif self.board_size == 9:
            return [(2, 2), (2, 6), (4, 4), (6, 2), (6, 6)]
        elif self.board_size == 8:
            return []
        else:
            return []
    
    def draw_stone(self, row, col, color):
        """绘制棋子"""
        x = self.padding + col * self.cell_size
        y = self.padding + row * self.cell_size
        r = self.cell_size // 2 - 2
        
        fill_color = 'black' if color == 'black' else 'white'
        outline_color = 'black'
        
        stone_id = self.create_oval(x - r, y - r, x + r, y + r, 
                                    fill=fill_color, outline=outline_color, width=2)
        self.stones[(row, col)] = stone_id
        
    def mark_last_move(self, row, col):
        """标记最后一手"""
        if self.last_move:
            self.delete(self.last_move)
        
        x = self.padding + col * self.cell_size
        y = self.padding + row * self.cell_size
        r = 5
        
        self.last_move = self.create_oval(x - r, y - r, x + r, y + r, 
                                         fill='red', outline='red')
    
    def show_valid_moves(self, valid_moves):
        """显示合法落子位置（黑白棋用）"""
        self.clear_valid_moves()
        for row, col in valid_moves:
            x = self.padding + col * self.cell_size
            y = self.padding + row * self.cell_size
            r = 5
            marker = self.create_oval(x - r, y - r, x + r, y + r,
                                     fill='green', outline='green', stipple='gray50')
            self.valid_move_markers.append(marker)
    
    def clear_valid_moves(self):
        """清除合法位置标记"""
        for marker in self.valid_move_markers:
            self.delete(marker)
        self.valid_move_markers.clear()
        
    def get_position_from_click(self, event):
        """从点击位置获取棋盘坐标"""
        x = event.x - self.padding
        y = event.y - self.padding
        
        col = round(x / self.cell_size)
        row = round(y / self.cell_size)
        
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            click_x = self.padding + col * self.cell_size
            click_y = self.padding + row * self.cell_size
            
            if abs(event.x - click_x) < self.cell_size // 2 and \
               abs(event.y - click_y) < self.cell_size // 2:
                return row, col
        
        return None
    
    def clear_stones(self):
        """清除所有棋子"""
        for stone_id in self.stones.values():
            self.delete(stone_id)
        self.stones.clear()
        if self.last_move:
            self.delete(self.last_move)
            self.last_move = None
        self.clear_valid_moves()


class LoginDialog(tk.Toplevel):
    """登录/注册对话框"""
    
    def __init__(self, parent, title, user_manager):
        super().__init__(parent)
        self.title(title)
        self.user_manager = user_manager
        self.result = None
        
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        self.wait_window(self)
    
    def _setup_ui(self):
        frame = tk.Frame(self, padx=20, pady=20)
        frame.pack()
        
        tk.Label(frame, text="用户名:").grid(row=0, column=0, sticky='e', pady=5)
        self.username_entry = tk.Entry(frame, width=20)
        self.username_entry.grid(row=0, column=1, pady=5)
        
        tk.Label(frame, text="密码:").grid(row=1, column=0, sticky='e', pady=5)
        self.password_entry = tk.Entry(frame, width=20, show='*')
        self.password_entry.grid(row=1, column=1, pady=5)
        
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="登录", command=self._login, width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="注册", command=self._do_register, width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=self.destroy, width=8).pack(side=tk.LEFT, padx=5)
    
    def _login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        try:
            self.result = self.user_manager.login(username, password)
            self.destroy()
        except ValueError as e:
            messagebox.showerror("登录失败", str(e))
    
    def _do_register(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        try:
            self.result = self.user_manager.register(username, password)
            messagebox.showinfo("成功", "注册成功！")
            self.destroy()
        except ValueError as e:
            messagebox.showerror("注册失败", str(e))


class NewGameDialog(tk.Toplevel):
    """新游戏对话框"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("开始新游戏")
        self.result = None
        
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        self.wait_window(self)
    
    def _setup_ui(self):
        frame = tk.Frame(self, padx=20, pady=20)
        frame.pack()
        
        # 游戏类型
        tk.Label(frame, text="游戏类型:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
        self.game_type = tk.StringVar(value='othello')
        types = [('五子棋', 'gomoku'), ('围棋', 'go'), ('黑白棋', 'othello')]
        for i, (text, value) in enumerate(types):
            tk.Radiobutton(frame, text=text, variable=self.game_type, value=value,
                          command=self._on_game_type_change).grid(row=0, column=i+1, padx=5)
        
        # 棋盘大小
        tk.Label(frame, text="棋盘大小:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='w', pady=5)
        self.board_size = tk.IntVar(value=8)
        self.size_spinbox = tk.Spinbox(frame, from_=8, to=19, textvariable=self.board_size, width=5)
        self.size_spinbox.grid(row=1, column=1, sticky='w', pady=5)
        
        # 黑方设置
        tk.Label(frame, text="黑方:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky='w', pady=5)
        self.black_type = tk.StringVar(value='human')
        tk.Radiobutton(frame, text="玩家", variable=self.black_type, value='human',
                      command=self._on_black_type_change).grid(row=2, column=1)
        tk.Radiobutton(frame, text="AI", variable=self.black_type, value='ai',
                      command=self._on_black_type_change).grid(row=2, column=2)
        
        tk.Label(frame, text="AI等级:").grid(row=2, column=3)
        self.black_ai_level = tk.IntVar(value=2)
        self.black_level_combo = ttk.Combobox(frame, textvariable=self.black_ai_level, 
                                              values=[1, 2, 3], width=3, state='disabled')
        self.black_level_combo.grid(row=2, column=4)
        
        # 白方设置
        tk.Label(frame, text="白方:", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky='w', pady=5)
        self.white_type = tk.StringVar(value='human')
        tk.Radiobutton(frame, text="玩家", variable=self.white_type, value='human',
                      command=self._on_white_type_change).grid(row=3, column=1)
        tk.Radiobutton(frame, text="AI", variable=self.white_type, value='ai',
                      command=self._on_white_type_change).grid(row=3, column=2)
        
        tk.Label(frame, text="AI等级:").grid(row=3, column=3)
        self.white_ai_level = tk.IntVar(value=2)
        self.white_level_combo = ttk.Combobox(frame, textvariable=self.white_ai_level,
                                              values=[1, 2, 3], width=3, state='disabled')
        self.white_level_combo.grid(row=3, column=4)
        
        # AI等级说明
        tk.Label(frame, text="AI等级: 1=随机, 2=评估函数, 3=MCTS", 
                font=('Arial', 8), fg='gray').grid(row=4, column=0, columnspan=5, pady=5)
        
        # 按钮
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=5, pady=15)
        
        tk.Button(btn_frame, text="开始游戏", command=self._start, 
                 bg='#4CAF50', fg='white', width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="取消", command=self.destroy, width=10).pack(side=tk.LEFT, padx=10)
    
    def _on_game_type_change(self):
        game_type = self.game_type.get()
        defaults = {'gomoku': 15, 'go': 19, 'othello': 8}
        self.board_size.set(defaults.get(game_type, 15))
    
    def _on_black_type_change(self):
        if self.black_type.get() == 'ai':
            self.black_level_combo.config(state='readonly')
        else:
            self.black_level_combo.config(state='disabled')
    
    def _on_white_type_change(self):
        if self.white_type.get() == 'ai':
            self.white_level_combo.config(state='readonly')
        else:
            self.white_level_combo.config(state='disabled')
    
    def _start(self):
        self.result = {
            'game_type': self.game_type.get(),
            'board_size': self.board_size.get(),
            'black_type': self.black_type.get(),
            'white_type': self.white_type.get(),
            'black_ai_level': self.black_ai_level.get(),
            'white_ai_level': self.white_ai_level.get()
        }
        self.destroy()


class ReplayControlDialog(tk.Toplevel):
    """回放控制窗口"""
    
    def __init__(self, parent, game_gui):
        super().__init__(parent)
        self.title("回放控制")
        self.game_gui = game_gui
        
        self.transient(parent)
        
        self._setup_ui()
        
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 400))
    
    def _setup_ui(self):
        frame = tk.Frame(self, padx=20, pady=10)
        frame.pack()
        
        # 进度信息
        self.progress_label = tk.Label(frame, text="步骤: 0/0", font=('Arial', 12))
        self.progress_label.pack(pady=5)
        
        # 进度条
        self.progress_scale = tk.Scale(frame, from_=0, to=100, orient=tk.HORIZONTAL, 
                                       length=200, command=self._on_scale_change)
        self.progress_scale.pack(pady=5)
        
        # 控制按钮
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="⏮", command=self._first, width=3).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="◀", command=self._prev, width=3).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="▶", command=self._next, width=3).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="⏭", command=self._last, width=3).pack(side=tk.LEFT, padx=2)
        
        # 退出按钮
        tk.Button(frame, text="退出回放", command=self._exit_replay,
                 bg='#F44336', fg='white').pack(pady=10)
    
    def update_progress(self, current, total):
        self.progress_label.config(text=f"步骤: {current}/{total}")
        if total > 0:
            self.progress_scale.config(to=total)
            self.progress_scale.set(current)
    
    def _on_scale_change(self, value):
        step = int(float(value))
        self.game_gui.platform.replay_goto(step)
        self.game_gui._update_display()
    
    def _first(self):
        self.game_gui.platform.replay_reset()
        self.game_gui._update_display()
        self._update()
    
    def _prev(self):
        self.game_gui.platform.replay_prev()
        self.game_gui._update_display()
        self._update()
    
    def _next(self):
        self.game_gui.platform.replay_next()
        self.game_gui._update_display()
        self._update()
    
    def _last(self):
        total = self.game_gui.platform.replayer.get_total_steps()
        self.game_gui.platform.replay_goto(total)
        self.game_gui._update_display()
        self._update()
    
    def _update(self):
        current = self.game_gui.platform.replayer.get_current_step()
        total = self.game_gui.platform.replayer.get_total_steps()
        self.update_progress(current, total)
    
    def _exit_replay(self):
        self.game_gui.platform.exit_replay()
        self.game_gui._update_display()
        self.game_gui.status_bar.config(text="已退出回放模式")
        self.destroy()


class ControlPanel(tk.Frame):
    """控制面板"""
    
    def __init__(self, master, game_gui):
        super().__init__(master, bg='#F0F0F0', relief=tk.RAISED, borderwidth=2)
        self.game_gui = game_gui
        
        self._setup_panel()
        
    def _setup_panel(self):
        """设置面板"""
        title = tk.Label(self, text="控制面板", font=('Arial', 14, 'bold'), bg='#F0F0F0')
        title.pack(pady=10)
        
        # 用户信息（简化版）
        user_frame = tk.LabelFrame(self, text="用户", bg='#F0F0F0', font=('Arial', 10, 'bold'))
        user_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.user_label = tk.Label(user_frame, text="未登录", bg='#F0F0F0', anchor='w', font=('Arial', 10))
        self.user_label.pack(fill=tk.X, padx=5, pady=5)
        
        self.login_btn = tk.Button(user_frame, text="登录 / 注册", 
                                command=self.game_gui._login_user,
                                bg='#2196F3', fg='white', font=('Arial', 9))
        self.login_btn.pack(fill=tk.X, padx=5, pady=2)
        
        self.logout_btn = tk.Button(user_frame, text="登出",
                                    command=self.game_gui._logout_user,
                                    bg='#757575', fg='white', font=('Arial', 9))
        self.logout_btn.pack(fill=tk.X, padx=5, pady=2)
        
        # 游戏信息
        info_frame = tk.LabelFrame(self, text="游戏信息", bg='#F0F0F0', font=('Arial', 10, 'bold'))
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.game_type_label = tk.Label(info_frame, text="游戏类型: -", bg='#F0F0F0', anchor='w')
        self.game_type_label.pack(fill=tk.X, padx=5, pady=2)

        self.player_label = tk.Label(info_frame, text="当前回合: -", bg='#F0F0F0', anchor='w')
        self.player_label.pack(fill=tk.X, padx=5, pady=2)

        # 添加这两个缺少的标签
        self.black_info_label = tk.Label(info_frame, text="黑方: -", bg='#F0F0F0', anchor='w')
        self.black_info_label.pack(fill=tk.X, padx=5, pady=2)

        self.white_info_label = tk.Label(info_frame, text="白方: -", bg='#F0F0F0', anchor='w')
        self.white_info_label.pack(fill=tk.X, padx=5, pady=2)

        self.undo_label = tk.Label(info_frame, text="悔棋次数: 0/5", bg='#F0F0F0', anchor='w')
        self.undo_label.pack(fill=tk.X, padx=5, pady=2)

        # 添加缺少的 move_count_label
        self.move_count_label = tk.Label(info_frame, text="落子数: 0", bg='#F0F0F0', anchor='w')
        self.move_count_label.pack(fill=tk.X, padx=5, pady=2)

        self.score_label = tk.Label(info_frame, text="比分: -", bg='#F0F0F0', anchor='w')
        self.score_label.pack(fill=tk.X, padx=5, pady=2)
        
        # 新游戏按钮
        tk.Button(self, text="🎮 开始新游戏", command=self.game_gui._new_game_dialog,
                bg='#4CAF50', fg='white', font=('Arial', 11, 'bold'), height=2).pack(fill=tk.X, padx=10, pady=10)
        
        # 操作按钮
        action_frame = tk.LabelFrame(self, text="游戏操作", bg='#F0F0F0', font=('Arial', 10, 'bold'))
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(action_frame, text="悔棋", command=self.game_gui._undo_move,
                bg='#FF9800', fg='white', font=('Arial', 10)).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(action_frame, text="弃权/虚着", command=self.game_gui._pass_move,
                bg='#795548', fg='white', font=('Arial', 10)).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(action_frame, text="认输", command=self.game_gui._resign,
                bg='#F44336', fg='white', font=('Arial', 10)).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(action_frame, text="重新开始", command=self.game_gui._reset_game,
                bg='#607D8B', fg='white', font=('Arial', 10)).pack(fill=tk.X, padx=5, pady=2)
        
        # 文件操作
        file_frame = tk.LabelFrame(self, text="存档/录像", bg='#F0F0F0', font=('Arial', 10, 'bold'))
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(file_frame, text="保存游戏", command=self.game_gui._save_game,
                bg='#00BCD4', fg='white', font=('Arial', 9)).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(file_frame, text="加载游戏", command=self.game_gui._load_game,
                bg='#009688', fg='white', font=('Arial', 9)).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(file_frame, text="保存录像", command=self.game_gui._save_replay,
                bg='#3F51B5', fg='white', font=('Arial', 9)).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(file_frame, text="回放录像", command=self.game_gui._load_replay,
                bg='#9C27B0', fg='white', font=('Arial', 9)).pack(fill=tk.X, padx=5, pady=2)
        
        # 落子记录
        history_frame = tk.LabelFrame(self, text="落子记录", bg='#F0F0F0', font=('Arial', 10, 'bold'))
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.history_text = scrolledtext.ScrolledText(history_frame, height=6, width=25,
                                                    font=('Courier', 9), state=tk.DISABLED)
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 排行榜
        tk.Button(self, text="🏆 排行榜", command=self.game_gui._show_leaderboard,
                bg='#FFD700', fg='black', font=('Arial', 10)).pack(fill=tk.X, padx=10, pady=5)
        
        # 退出
        tk.Button(self, text="退出程序", command=self.game_gui.window.quit,
                bg='#424242', fg='white', font=('Arial', 10, 'bold')).pack(fill=tk.X, padx=10, pady=10)
    
    def update_user_display(self, user):
        """更新用户显示"""
        if user:
            self.user_label.config(text=f"{user.username}\n{user.wins}胜 / {user.games}场")
            self.login_btn.config(state=tk.DISABLED)
            self.logout_btn.config(state=tk.NORMAL)
        else:
            self.user_label.config(text="未登录")
            self.login_btn.config(state=tk.NORMAL)
            self.logout_btn.config(state=tk.DISABLED)
        
    def update_info(self, game_state):
        """更新信息显示"""
        if game_state is None:
            self.game_type_label.config(text="游戏类型: -")
            self.player_label.config(text="当前回合: -")
            self.undo_label.config(text="悔棋次数: 0/5")
            self.move_count_label.config(text="落子数: 0")
            self.score_label.config(text="比分: -")
            return
        
        # 游戏类型
        game_type_name = {
            'gomoku': '五子棋',
            'go': '围棋',
            'othello': '黑白棋'
        }.get(self.game_gui.platform.current_game.get_game_type(), '未知')
        self.game_type_label.config(text=f"游戏类型: {game_type_name}")
        
        # 当前玩家/游戏结束
        if game_state.get('replay_mode'):
            step = game_state.get('replay_step', 0)
            total = game_state.get('replay_total', 0)
            self.player_label.config(text=f"[回放] {step}/{total}")
        elif game_state['game_over']:
            if game_state['winner'] == 'draw':
                self.player_label.config(text="游戏结束: 平局")
            else:
                winner = "黑方" if game_state['winner'] == 'black' else "白方"
                self.player_label.config(text=f"获胜方: {winner}")
        else:
            current = "黑方" if game_state['current_player'] == 'black' else "白方"
            # 显示是AI还是玩家
            current_player = game_state.get('black_player') if game_state['current_player'] == 'black' else game_state.get('white_player')
            if current_player and not current_player.is_human():
                current += " (AI)"
            self.player_label.config(text=f"当前回合: {current}")
        
        self.undo_label.config(text=f"悔棋次数: {game_state['undo_count']}/{game_state['max_undo_count']}")
        
        move_count = len(self.game_gui.platform.current_game.move_history)
        self.move_count_label.config(text=f"落子数: {move_count}")
        
        # 显示比分（黑白棋/围棋）
        game = self.game_gui.platform.current_game
        if isinstance(game, OthelloGame):
            black = game.board.count_stones('black')
            white = game.board.count_stones('white')
            self.score_label.config(text=f"比分: 黑{black} - 白{white}")
        elif isinstance(game, GoGame):
            captured = game.captured_count
            self.score_label.config(text=f"提子: 黑{captured['black']} 白{captured['white']}")
        else:
            self.score_label.config(text="比分: -")
    
    def update_user_info(self, black_info, white_info):
        """更新玩家信息"""
        self.black_info_label.config(text=f"黑方: {black_info or '-'}")
        self.white_info_label.config(text=f"白方: {white_info or '-'}")
        
    def add_move_to_history(self, move_num, player, row, col):
        """添加落子记录"""
        self.history_text.config(state=tk.NORMAL)
        player_str = "黑" if player == 'black' else "白"
        move_str = f"{move_num}. {player_str}: {chr(65 + col)}{row + 1}\n"
        self.history_text.insert(tk.END, move_str)
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)
        
    def add_pass_to_history(self, move_num, player):
        """添加弃权记录"""
        self.history_text.config(state=tk.NORMAL)
        player_str = "黑" if player == 'black' else "白"
        move_str = f"{move_num}. {player_str}: 弃权\n"
        self.history_text.insert(tk.END, move_str)
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)
        
    def clear_history(self):
        """清除落子记录"""
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        self.history_text.config(state=tk.DISABLED)


class GameGUI:
    """游戏图形界面"""
    
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("棋类对战平台 v2.0")
        self.window.resizable(True, True)
        
        self.platform = GamePlatform()
        self.canvas = None
        self.control_panel = None
        self.replay_dialog = None
        
        # 当前登录用户（只有一个）
        self.current_user = None
        
        # 网络对战相关
        self.network_mode = False
        self.network_client = None
        self.server = None
        self.network_move_count = 0
        
        self._setup_menu()
        self._setup_main_layout()
        self._setup_status_bar()

    def _setup_menu(self):
        """设置菜单"""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # 游戏菜单
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="游戏", menu=game_menu)
        game_menu.add_command(label="新游戏...", command=self._new_game_dialog)
        game_menu.add_separator()
        game_menu.add_command(label="保存游戏", command=self._save_game)
        game_menu.add_command(label="加载游戏", command=self._load_game)
        game_menu.add_separator()
        game_menu.add_command(label="保存录像", command=self._save_replay)
        game_menu.add_command(label="回放录像", command=self._load_replay)
        game_menu.add_separator()
        game_menu.add_command(label="退出", command=self.window.quit)
        
        # 操作菜单
        action_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="操作", menu=action_menu)
        action_menu.add_command(label="悔棋", command=self._undo_move)
        action_menu.add_command(label="弃权/虚着", command=self._pass_move)
        action_menu.add_command(label="认输", command=self._resign)
        action_menu.add_command(label="重新开始", command=self._reset_game)
        
        # 用户菜单
        user_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="用户", menu=user_menu)
        user_menu.add_command(label="登录 / 注册", command=self._login_user)
        user_menu.add_command(label="登出", command=self._logout_user)
        user_menu.add_separator()
        user_menu.add_command(label="排行榜", command=self._show_leaderboard)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="游戏规则", command=self._show_rules)
        help_menu.add_command(label="关于", command=self._show_about)

        network_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="网络对战", menu=network_menu)
        network_menu.add_command(label="创建房间(服务器)", command=self._start_server)
        network_menu.add_command(label="加入房间(客户端)", command=self._connect_to_server)
        network_menu.add_separator()
        network_menu.add_command(label="断开连接", command=self._disconnect_network)
        
    def _setup_main_layout(self):
        """设置主布局"""
        main_container = tk.Frame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：棋盘
        left_frame = tk.Frame(main_container, bg='#F5F5DC')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas_frame = tk.Frame(left_frame, bg='#F5F5DC')
        self.canvas_frame.pack(expand=True)
        
        # 右侧：控制面板
        self.control_panel = ControlPanel(main_container, self)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
    def _setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = tk.Label(self.window, text="欢迎使用棋类对战平台！点击「开始新游戏」开始", 
                                  bd=1, relief=tk.SUNKEN, anchor=tk.W, font=('Arial', 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _new_game_dialog(self):
        """打开新游戏对话框"""
        dialog = NewGameDialog(self.window)
        if dialog.result:
            self._start_game(dialog.result)
    
    def _start_game(self, config):
        """开始游戏"""
        try:
            # 确定用户
            user_for_game = self.current_user  # 可以是None（游客）
            
            self.platform.create_game(
                game_type=config['game_type'],
                board_size=config['board_size'],
                black_player_type=config['black_type'],
                white_player_type=config['white_type'],
                black_ai_level=config['black_ai_level'],
                white_ai_level=config['white_ai_level'],
                black_user=user_for_game if config['black_type'] == 'human' else None,
                white_user=user_for_game if config['white_type'] == 'human' and config['black_type'] != 'human' else None
            )
            
            self._create_canvas(config['board_size'])
            self.control_panel.clear_history()
            self._update_display()
            
            game_names = {'gomoku': '五子棋', 'go': '围棋', 'othello': '黑白棋'}
            game_name = game_names.get(config['game_type'], config['game_type'])
            self.status_bar.config(text=f"开始 {game_name} 游戏")
            
            self._check_ai_turn()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            
    def _create_canvas(self, size):
        """创建棋盘画布"""
        if self.canvas:
            self.canvas.destroy()
        
        self.canvas = ChessBoardCanvas(self.canvas_frame, size=size)
        self.canvas.pack()
        self.canvas.draw_board()
        self.canvas.bind('<Button-1>', self._on_canvas_click)
        
    def _on_canvas_click(self, event):
        """棋盘点击事件"""
        # ========== 网络模式优先处理 ==========
        if hasattr(self, 'network_mode') and self.network_mode:
            if self.network_client and self.network_client.connected:
                game_state = self.network_client.get_game_state()
                
                if game_state.get('game_over'):
                    self.status_bar.config(text="游戏已结束")
                    return
                
                if not game_state.get('is_my_turn'):
                    self.status_bar.config(text="不是你的回合")
                    return
                
                pos = self.canvas.get_position_from_click(event)
                if pos:
                    row, col = pos
                    print(f"[GUI] 网络落子: ({row}, {col})")
                    self.network_client.make_move(row, col)
            return
        
        # ========== 本地模式 ==========
        if not self.platform.current_game:
            return
        if self.platform.current_game.game_over:
            return
        
        state = self.platform.get_game_state()
        current_player = state['current_player']
        
        if current_player == 'black':
            player = state.get('black_player')
        else:
            player = state.get('white_player')
        
        if player and not player.is_human():
            self.status_bar.config(text="AI正在思考，请稍候...")
            return
        
        pos = self.canvas.get_position_from_click(event)
        if not pos:
            return
        
        row, col = pos
        
        try:
            player.set_move(row, col)
            self.platform.make_move(row, col)
            
            move_num = len(self.platform.current_game.move_history)
            self.control_panel.add_move_to_history(move_num, current_player, row, col)
            
            self._update_display()
            
            if self.platform.current_game.game_over:
                self._show_game_over()
            else:
                self.window.after(300, self._check_ai_turn)
                
        except ValueError as e:
            self.status_bar.config(text=str(e))



    def _check_ai_turn(self):
        """检查是否轮到AI落子 - 修复版：逐步显示"""
        if not self.platform.current_game:
            return
        if self.platform.current_game.game_over:
            return
        if hasattr(self, 'network_mode') and self.network_mode:
            return
        
        state = self.platform.get_game_state()
        current_player = state['current_player']
        
        # 判断当前是哪个玩家
        if current_player == 'black':
            player = state.get('black_player')
        else:
            player = state.get('white_player')
        
        # 如果是AI玩家
        if player and not player.is_human():
            # 更新状态栏显示AI正在思考
            ai_name = f"AI Lv.{player.level}" if hasattr(player, 'level') else "AI"
            color_name = "黑方" if current_player == 'black' else "白方"
            self.status_bar.config(text=f"{color_name} {ai_name} 正在思考...")
            self.window.update()  # 强制更新UI
            
            # 使用 after 延迟执行AI落子，让UI有时间更新
            self.window.after(100, self._execute_ai_move)


    def _execute_ai_move(self):
        """执行AI落子 - 分离出来以便异步调用"""
        if not self.platform.current_game:
            return
        if self.platform.current_game.game_over:
            return
        
        state = self.platform.get_game_state()
        current_player = state['current_player']
        
        if current_player == 'black':
            player = state.get('black_player')
        else:
            player = state.get('white_player')
        
        if player and not player.is_human():
            try:
                # 获取AI的落子
                move = player.get_move(self.platform.current_game)
                
                if move:
                    row, col = move
                    # 执行落子
                    self.platform.make_move(row, col)
                    
                    # 记录到历史
                    move_num = len(self.platform.current_game.move_history)
                    self.control_panel.add_move_to_history(move_num, current_player, row, col)
                    
                    # 更新显示
                    self._update_display()
                    
                    # 检查游戏是否结束
                    if self.platform.current_game.game_over:
                        self._show_game_over()
                    else:
                        # 延迟500ms后检查下一个AI（让玩家能看到棋子）
                        self.window.after(500, self._check_ai_turn)
                else:
                    self.status_bar.config(text="AI无法落子")
                    
            except Exception as e:
                self.status_bar.config(text=f"AI出错: {e}")
                import traceback
                traceback.print_exc()
                
    def _update_display(self):
        """更新显示"""
        if not self.platform.current_game:
            self.control_panel.update_info(None)
            return
        
        state = self.platform.get_game_state()
        self.control_panel.update_info(state)
        
        # 修复：获取玩家信息
        black_player = state.get('black_player')
        white_player = state.get('white_player')
        
        black_info = "-"
        white_info = "-"
        
        if black_player:
            if black_player.is_human():
                black_info = black_player.user.username if black_player.user else "玩家"
            else:
                # 修复：使用 getattr 安全获取 AI 等级
                level = getattr(black_player, 'level', None) or getattr(black_player, 'ai_level', None) or '?'
                black_info = f"AI Lv.{level}"
        
        if white_player:
            if white_player.is_human():
                white_info = white_player.user.username if white_player.user else "玩家"
            else:
                # 修复：使用 getattr 安全获取 AI 等级
                level = getattr(white_player, 'level', None) or getattr(white_player, 'ai_level', None) or '?'
                white_info = f"AI Lv.{level}"
        
        self.control_panel.update_user_info(black_info, white_info)
        
        if self.canvas:
            self.canvas.clear_stones()
            board = state['board']
            for i in range(board.size):
                for j in range(board.size):
                    stone = board.get_stone(i, j)
                    if stone:
                        self.canvas.draw_stone(i, j, stone)
            
            # 标记最后一手
            if self.platform.current_game.move_history:
                last_move = self.platform.current_game.move_history[-1]
                if last_move.get('row') is not None:
                    self.canvas.mark_last_move(last_move['row'], last_move['col'])
            
            # 黑白棋显示合法位置
            if isinstance(self.platform.current_game, OthelloGame) and not state['game_over']:
                if not self.platform.replay_mode:
                    valid_moves = self.platform.current_game.get_valid_moves()
                    self.canvas.show_valid_moves(valid_moves)
                    
    def _undo_move(self):
        """悔棋"""
        # 网络模式
        if hasattr(self, 'network_mode') and self.network_mode:
            if self.network_client and self.network_client.connected:
                self.network_client.request_undo()
                self.status_bar.config(text="已发送悔棋请求，等待对方同意...")
            return
        
        # 本地模式
        try:
            self.platform.undo_move()
            self._update_display()
            self.status_bar.config(text="悔棋成功")
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            
    def _pass_move(self):
        """弃权/虚着"""
        # 网络模式
        if hasattr(self, 'network_mode') and self.network_mode:
            if self.network_client and self.network_client.connected:
                if not self.network_client.get_game_state().get('is_my_turn'):
                    messagebox.showwarning("提示", "不是你的回合")
                    return
                self.network_client.pass_move()
                self.status_bar.config(text="已弃权")
            return
        
        # 本地模式
        try:
            current_player = self.platform.current_game.current_player
            move_num = len(self.platform.current_game.move_history) + 1
            self.platform.pass_move()
            self.control_panel.add_pass_to_history(move_num, current_player)
            self._update_display()
            self.status_bar.config(text="弃权")
            if self.platform.current_game.game_over:
                self._show_game_over()
            else:
                self._check_ai_turn()
        except ValueError as e:
            messagebox.showerror("错误", str(e))
            
    def _resign(self):
        """认输"""
        # 网络模式
        if hasattr(self, 'network_mode') and self.network_mode:
            if self.network_client and self.network_client.connected:
                if messagebox.askyesno("确认", "确定要认输吗？"):
                    self.network_client.resign()
                    self.status_bar.config(text="你已认输")
            return
        
        # 本地模式
        if not self.platform.current_game:
            return
        if messagebox.askyesno("确认", "确定要认输吗？"):
            try:
                self.platform.resign()
                self._update_display()
                self._show_game_over()
            except ValueError as e:
                messagebox.showerror("错误", str(e))
                
    def _reset_game(self):
        """重新开始"""
        # 网络模式下暂不支持重新开始
        if hasattr(self, 'network_mode') and self.network_mode:
            messagebox.showinfo("提示", "网络模式下请重新创建游戏")
            return
        
        # 本地模式
        if not self.platform.current_game:
            return
        if messagebox.askyesno("确认", "确定要重新开始吗？"):
            try:
                self.platform.reset_game()
                self.control_panel.clear_history()
                self._update_display()
                self.status_bar.config(text="游戏已重新开始")
                self._check_ai_turn()
            except ValueError as e:
                messagebox.showerror("错误", str(e))
                
    def _save_game(self):
        """保存游戏"""
        # 网络模式
        if hasattr(self, 'network_mode') and self.network_mode:
            messagebox.showinfo("提示", "网络对战模式下暂不支持保存游戏")
            return
        
        # 本地模式
        if not self.platform.current_game:
            messagebox.showwarning("提示", "没有正在进行的游戏")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.platform.save_to_file(filename)
                self.status_bar.config(text=f"游戏已保存: {filename}")
                messagebox.showinfo("成功", "游戏保存成功")
            except ValueError as e:
                messagebox.showerror("错误", str(e))
                
    def _load_game(self):
        """加载游戏"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.platform.load_from_file(filename)
                state = self.platform.get_game_state()
                self._create_canvas(state['board'].size)
                self.control_panel.clear_history()
                
                # 重建落子记录
                for i, move in enumerate(self.platform.current_game.move_history, 1):
                    if move.get('pass') or move.get('type') == 'pass':
                        self.control_panel.add_pass_to_history(i, move['player'])
                    else:
                        self.control_panel.add_move_to_history(i, move['player'], 
                                                              move['row'], move['col'])
                
                self._update_display()
                self.status_bar.config(text=f"游戏已加载: {filename}")
            except ValueError as e:
                messagebox.showerror("错误", str(e))
    
    def _save_replay(self):
        """保存录像"""
        if not self.platform.current_game:
            messagebox.showwarning("提示", "没有可保存的录像")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".replay",
            filetypes=[("Replay files", "*.replay"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.platform.save_replay(filename)
                self.status_bar.config(text=f"录像已保存: {filename}")
                messagebox.showinfo("成功", "录像保存成功")
            except ValueError as e:
                messagebox.showerror("错误", str(e))
    
    def _load_replay(self):
        """加载并回放录像"""
        filename = filedialog.askopenfilename(
            filetypes=[("Replay files", "*.replay"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.platform.load_replay(filename)
                state = self.platform.get_game_state()
                self._create_canvas(state['board'].size)
                self._update_display()
                
                # 打开回放控制窗口
                self.replay_dialog = ReplayControlDialog(self.window, self)
                total = self.platform.replayer.get_total_steps()
                self.replay_dialog.update_progress(0, total)
                
                self.status_bar.config(text=f"已加载录像，进入回放模式")
            except Exception as e:
                messagebox.showerror("错误", str(e))
    
    def _login_user(self):
        """用户登录"""
        if self.current_user:
            messagebox.showinfo("提示", f"已登录为: {self.current_user.username}")
            return
        
        dialog = LoginDialog(self.window, "登录 / 注册", self.platform.user_manager)
        if dialog.result:
            self.current_user = dialog.result
            self.control_panel.update_user_display(self.current_user)
            self.status_bar.config(text=f"欢迎, {self.current_user.username}!")
    
    def _logout_user(self):
        """用户登出"""
        if not self.current_user:
            return
        
        if messagebox.askyesno("确认", f"确定要登出 {self.current_user.username} 吗？"):
            self.current_user = None
            self.control_panel.update_user_display(None)
            self.status_bar.config(text="已登出")
    
    def _show_leaderboard(self):
        """显示排行榜"""
        leaderboard = self.platform.get_leaderboard(10)
        
        dialog = tk.Toplevel(self.window)
        dialog.title("🏆 排行榜")
        dialog.transient(self.window)
        
        frame = tk.Frame(dialog, padx=20, pady=20)
        frame.pack()
        
        tk.Label(frame, text="排行榜", font=('Arial', 16, 'bold')).pack(pady=10)
        
        if not leaderboard:
            tk.Label(frame, text="暂无数据", font=('Arial', 12)).pack(pady=20)
        else:
            for i, user in enumerate(leaderboard, 1):
                win_rate = user.get_win_rate() * 100
                text = f"{i}. {user.username}: {user.wins}胜/{user.games}场 ({win_rate:.1f}%)"
                tk.Label(frame, text=text, font=('Arial', 11)).pack(anchor='w', pady=2)
        
        tk.Button(frame, text="关闭", command=dialog.destroy).pack(pady=10)
                
    def _show_game_over(self):
        """显示游戏结束"""
        state = self.platform.get_game_state()
        
        if hasattr(self.platform.current_game, 'final_score'):
            score = self.platform.current_game.final_score
            if state['winner'] == 'draw':
                message = f"游戏结束 - 平局\n\n"
            else:
                winner = "黑方" if state['winner'] == 'black' else "白方"
                message = f"游戏结束\n\n{winner} 获胜！\n\n"
            
            message += f"黑方: {score['black']} 子\n"
            message += f"白方: {score['white']} 子"
        else:
            if state['winner'] == 'draw':
                message = "游戏结束\n\n平局"
            else:
                winner = "黑方" if state['winner'] == 'black' else "白方"
                message = f"游戏结束\n\n{winner} 获胜！"
        
        messagebox.showinfo("游戏结束", message)
        
    def _show_rules(self):
        """显示规则"""
        rules = """【五子棋规则】
    
    
- 双方交替落子，黑先
- 先连成五子者获胜
- 棋盘下满为平局

【围棋规则】
- 双方交替落子或虚着
- 无气的棋子会被提掉
- 双方均虚着后计算胜负
- 采用中国规则（贴3.75子）

【黑白棋规则】
- 双方交替落子，黑先
- 落子必须能翻转对手棋子
- 被夹住的对方棋子会翻转
- 无法落子时自动弃权
- 棋盘填满或双方都无法落子时结束
- 棋子多者获胜

【AI等级说明】
- 1级: 随机落子
- 2级: 评估函数（位置权重+策略）
- 3级: 蒙特卡洛树搜索(MCTS)
        """
        messagebox.showinfo("游戏规则", rules)
        
    def _show_about(self):
        """显示关于"""
        about = """棋类对战平台 v2.0

支持游戏：五子棋、围棋、黑白棋

主要功能：
- 人人对战 / 人机对战 / AI对战
- 三级AI算法（随机/评估/MCTS）
- 用户账户与战绩管理
- 游戏存档与加载
- 录像保存与回放
- 图形化界面

设计模式：
工厂模式、策略模式、单例模式、
观察者模式、外观模式、建造者模式
        """
        messagebox.showinfo("关于", about)
    
    def _start_server(self):
        """启动服务器"""
        if not self.current_user:
            messagebox.showwarning("提示", "请先登录账号才能创建房间！")
            return
        
        from game_platform.network.server import GameServer
        from game_platform.network.client import NetworkClient
        
        dialog = tk.Toplevel(self.window)
        dialog.title("创建房间 (服务器)")
        dialog.transient(self.window)
        
        frame = tk.Frame(dialog, padx=20, pady=20)
        frame.pack()
        
        tk.Label(frame, text="端口:").grid(row=0, column=0, sticky='e', pady=5)
        port_entry = tk.Entry(frame, width=10)
        port_entry.insert(0, "9999")
        port_entry.grid(row=0, column=1, pady=5, sticky='w')
        
        tk.Label(frame, text="用户:").grid(row=1, column=0, sticky='e', pady=5)
        user_label = tk.Label(frame, text=f"{self.current_user.username} ({self.current_user.wins}胜/{self.current_user.games}场)", fg='blue')
        user_label.grid(row=1, column=1, pady=5, sticky='w')
        
        log_text = scrolledtext.ScrolledText(frame, height=8, width=40, state=tk.DISABLED)
        log_text.grid(row=2, column=0, columnspan=2, pady=10)
        
        status_label = tk.Label(frame, text="", fg='blue')
        status_label.grid(row=3, column=0, columnspan=2)
        
        self.server = None
        check_color_job = [None]
        
        def add_log(msg):
            try:
                if dialog.winfo_exists():
                    log_text.config(state=tk.NORMAL)
                    log_text.insert(tk.END, msg + "\n")
                    log_text.see(tk.END)
                    log_text.config(state=tk.DISABLED)
            except:
                pass
        
        def check_color_update():
            if self.network_client and self.network_client.connected:
                color = self.network_client.color
                if color:
                    color_name = "黑" if color == 'black' else "白"
                    status_label.config(text=f"已就绪! 你是 {color_name} 方，等待对手连接...", fg='green')
                    self.status_bar.config(text=f"服务器运行中，你是{color_name}方")
                    return
                else:
                    check_color_job[0] = dialog.after(200, check_color_update)
        
        def start():
            try:
                port = int(port_entry.get())
                
                # 1. 启动服务器
                self.server = GameServer('0.0.0.0', port)
                self.server.on_log = add_log
                
                server_thread = threading.Thread(target=self.server.start)
                server_thread.daemon = True
                server_thread.start()
                
                add_log(f"服务器已启动，端口 {port}")
                add_log(f"玩家: {self.current_user.username}")
                add_log("正在自动连接...")
                
                # 2. 等待服务器启动后自动连接
                dialog.after(500, lambda: auto_connect(port))
                
            except Exception as e:
                messagebox.showerror("错误", str(e))
        
        def auto_connect(port):
            try:
                self.network_client = NetworkClient()
                self.network_client.on_message = self._on_network_message
                self.network_client.on_state_update = self._on_network_state_update
                self.network_client.on_game_start = self._on_network_game_start
                self.network_client.on_game_over = self._on_network_game_over
                self.network_client.on_undo_request = self._on_network_undo_request
                
                # 使用登录的用户名
                self.network_client.connect('localhost', port, self.current_user.username, 'black')
                self.network_mode = True
                self.network_move_count = 0  # 初始化网络模式落子计数
                
                add_log(f"已连接为: {self.current_user.username}")
                status_label.config(text="已连接，等待分配颜色...", fg='blue')
                
                check_color_job[0] = dialog.after(300, check_color_update)
                
            except Exception as e:
                add_log(f"自动连接失败: {e}")
                status_label.config(text=f"连接失败: {e}", fg='red')
        
        def create_game():
            if not self.network_client or not self.network_client.connected:
                messagebox.showerror("错误", "请先启动服务器")
                return
            
            if not self.network_client.color:
                messagebox.showerror("错误", "等待连接就绪...")
                return
            
            game_dialog = tk.Toplevel(dialog)
            game_dialog.title("创建游戏")
            game_dialog.transient(dialog)
            
            gframe = tk.Frame(game_dialog, padx=20, pady=20)
            gframe.pack()
            
            tk.Label(gframe, text="游戏类型:").grid(row=0, column=0, sticky='w')
            game_type_var = tk.StringVar(value='othello')
            tk.Radiobutton(gframe, text="五子棋", variable=game_type_var, value='gomoku').grid(row=0, column=1)
            tk.Radiobutton(gframe, text="围棋", variable=game_type_var, value='go').grid(row=0, column=2)
            tk.Radiobutton(gframe, text="黑白棋", variable=game_type_var, value='othello').grid(row=0, column=3)
            
            tk.Label(gframe, text="棋盘大小:").grid(row=1, column=0, sticky='w', pady=10)
            size_var = tk.IntVar(value=8)
            tk.Spinbox(gframe, from_=8, to=19, textvariable=size_var, width=5).grid(row=1, column=1, sticky='w')
            
            def do_create():
                self.network_client.create_game(game_type_var.get(), size_var.get())
                game_dialog.destroy()
                add_log(f"游戏已创建: {game_type_var.get()} {size_var.get()}x{size_var.get()}")
                # 清空落子记录
                self.control_panel.clear_history()
                self.network_move_count = 0
            
            tk.Button(gframe, text="创建游戏", command=do_create, bg='#4CAF50', fg='white').grid(row=2, column=0, columnspan=4, pady=15)
        
        def stop():
            if check_color_job[0]:
                try:
                    dialog.after_cancel(check_color_job[0])
                except:
                    pass
            
            if self.network_client:
                self.network_client.disconnect()
                self.network_client = None
            
            if self.server:
                self.server.on_log = None
                self.server.stop()
                self.server = None
            
            self.network_mode = False
            self.status_bar.config(text="服务器已停止")
            dialog.destroy()
        
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="启动服务器", command=start, bg='#4CAF50', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="创建游戏", command=create_game, bg='#2196F3', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="停止并关闭", command=stop).pack(side=tk.LEFT, padx=5)
        
        dialog.protocol("WM_DELETE_WINDOW", stop)
        
    def _connect_to_server(self):
        """连接到服务器"""
        if not self.current_user:
            messagebox.showwarning("提示", "请先登录账号才能加入房间！")
            return
        
        from game_platform.network.client import NetworkClient
        
        dialog = tk.Toplevel(self.window)
        dialog.title("加入房间")
        dialog.transient(self.window)
        
        frame = tk.Frame(dialog, padx=20, pady=20)
        frame.pack()
        
        # 服务器地址
        tk.Label(frame, text="服务器地址:").grid(row=0, column=0, sticky='e', pady=5)
        host_entry = tk.Entry(frame, width=15)
        host_entry.insert(0, "localhost")
        host_entry.grid(row=0, column=1, pady=5)
        
        # 端口
        tk.Label(frame, text="端口:").grid(row=1, column=0, sticky='e', pady=5)
        port_entry = tk.Entry(frame, width=15)
        port_entry.insert(0, "9999")
        port_entry.grid(row=1, column=1, pady=5)
        
        # 显示当前用户
        tk.Label(frame, text="用户:").grid(row=2, column=0, sticky='e', pady=5)
        tk.Label(frame, text=f"{self.current_user.username} ({self.current_user.wins}胜/{self.current_user.games}场)", 
                fg='blue').grid(row=2, column=1, pady=5, sticky='w')
        
        status_label = tk.Label(frame, text="", fg='blue')
        status_label.grid(row=3, column=0, columnspan=2, pady=5)
        
        check_color_job = [None]
        
        def check_color_update():
            if self.network_client and self.network_client.connected:
                color = self.network_client.color
                if color:
                    color_name = "黑" if color == 'black' else "白"
                    status_label.config(text=f"已连接! 你是 {color_name} 方", fg='green')
                    self.status_bar.config(text=f"已连接，你是{color_name}方")
                    return
                else:
                    check_color_job[0] = dialog.after(200, check_color_update)
        
        def connect():
            host = host_entry.get().strip()
            port = port_entry.get().strip()
            
            if not host or not port:
                messagebox.showerror("错误", "请输入服务器地址和端口")
                return
            
            try:
                status_label.config(text="正在连接...", fg='blue')
                dialog.update()
                
                self.network_client = NetworkClient()
                self.network_client.on_message = self._on_network_message
                self.network_client.on_state_update = self._on_network_state_update
                self.network_client.on_game_start = self._on_network_game_start
                self.network_client.on_game_over = self._on_network_game_over
                self.network_client.on_undo_request = self._on_network_undo_request
                
                self.network_client.connect(host, port, self.current_user.username, 'white')
                self.network_mode = True
                self.network_move_count = 0
                
                status_label.config(text="已连接，等待分配颜色...", fg='blue')
                check_color_job[0] = dialog.after(300, check_color_update)
                
                self.control_panel.clear_history()
                
            except Exception as e:
                status_label.config(text=f"连接失败: {e}", fg='red')
                self.network_client = None
                self.network_mode = False
        
        def create_network_game():
            if not self.network_client or not self.network_client.connected:
                messagebox.showerror("错误", "请先连接服务器")
                return
            
            if not self.network_client.color:
                messagebox.showerror("错误", "等待颜色分配...")
                return
            
            game_dialog = tk.Toplevel(dialog)
            game_dialog.title("创建网络游戏")
            game_dialog.transient(dialog)
            
            gframe = tk.Frame(game_dialog, padx=20, pady=20)
            gframe.pack()
            
            tk.Label(gframe, text="游戏类型:").grid(row=0, column=0, sticky='w')
            game_type_var = tk.StringVar(value='othello')
            tk.Radiobutton(gframe, text="五子棋", variable=game_type_var, value='gomoku').grid(row=0, column=1)
            tk.Radiobutton(gframe, text="围棋", variable=game_type_var, value='go').grid(row=0, column=2)
            tk.Radiobutton(gframe, text="黑白棋", variable=game_type_var, value='othello').grid(row=0, column=3)
            
            tk.Label(gframe, text="棋盘大小:").grid(row=1, column=0, sticky='w', pady=10)
            size_var = tk.IntVar(value=8)
            tk.Spinbox(gframe, from_=8, to=19, textvariable=size_var, width=5).grid(row=1, column=1, sticky='w')
            
            def do_create():
                self.network_client.create_game(game_type_var.get(), size_var.get())
                game_dialog.destroy()
                status_label.config(text="游戏已创建!", fg='green')
                self.control_panel.clear_history()
                self.network_move_count = 0
            
            tk.Button(gframe, text="创建游戏", command=do_create, 
                    bg='#4CAF50', fg='white').grid(row=2, column=0, columnspan=4, pady=15)
        
        def disconnect_and_close():
            if check_color_job[0]:
                try:
                    dialog.after_cancel(check_color_job[0])
                except:
                    pass
            
            if self.network_client:
                self.network_client.disconnect()
                self.network_client = None
            self.network_mode = False
            self.status_bar.config(text="已断开连接")
            dialog.destroy()
        
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=15)
        
        tk.Button(btn_frame, text="连接", command=connect, 
                bg='#4CAF50', fg='white', width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="创建游戏", command=create_network_game, 
                bg='#2196F3', fg='white', width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="关闭", command=disconnect_and_close, width=8).pack(side=tk.LEFT, padx=5)
        
        dialog.protocol("WM_DELETE_WINDOW", disconnect_and_close)
    
    def _disconnect_network(self):
        """断开网络连接"""
        if hasattr(self, 'network_client') and self.network_client:
            self.network_client.disconnect()
            self.network_client = None
        if hasattr(self, 'server') and self.server:
            self.server.stop()
            self.server = None
        self.network_mode = False
        self.status_bar.config(text="已断开网络连接")
    
    def _on_network_message(self, msg_type, message):
        """网络消息回调"""
        if message:
            self.status_bar.config(text=message)
    
    def _on_network_state_update(self, state):
        """网络状态更新回调"""
        self.window.after(0, self._update_network_display, state)
    
    def _update_network_display(self, state):
        """更新网络游戏显示"""
        board = state.get('board')
        
        if board is None:
            return
        
        # 如果画布还没创建或大小不匹配，先创建
        if self.canvas is None or self.canvas.board_size != board.size:
            self._create_canvas(board.size)
        
        # 统计当前棋子数，用于判断是否有新落子
        current_stone_count = 0
        last_stone_pos = None
        last_stone_color = None
        
        # 清除并重绘棋子
        self.canvas.clear_stones()
        
        for i in range(board.size):
            for j in range(board.size):
                stone = board.get_stone(i, j)
                if stone:
                    self.canvas.draw_stone(i, j, stone)
                    current_stone_count += 1
                    last_stone_pos = (i, j)
                    last_stone_color = stone
        
        # 检测新落子并记录
        if not hasattr(self, 'network_move_count'):
            self.network_move_count = 0
        
        if current_stone_count > self.network_move_count:
            # 有新落子
            if last_stone_pos:
                row, col = last_stone_pos
                self.canvas.mark_last_move(row, col)
                
                # 添加到落子记录
                # 需要找出最后落子的是谁（根据当前回合反推）
                current_player = state.get('current_player')
                # 当前是谁的回合，说明刚才落子的是对方
                last_player = 'white' if current_player == 'black' else 'black'
                
                self.control_panel.add_move_to_history(current_stone_count, last_player, row, col)
            
            self.network_move_count = current_stone_count
        
        # 更新控制面板信息
        self._update_network_control_panel(state)
        
        # 更新状态栏
        if state.get('game_over'):
            winner = state.get('winner')
            if winner == 'draw':
                self.status_bar.config(text="游戏结束: 平局")
            else:
                winner_name = "黑方" if winner == 'black' else "白方"
                self.status_bar.config(text=f"游戏结束: {winner_name}获胜!")
        else:
            is_my_turn = state.get('is_my_turn', False)
            current = "黑方" if state.get('current_player') == 'black' else "白方"
            
            if is_my_turn:
                self.status_bar.config(text=f"轮到你落子 ({current})")
            else:
                self.status_bar.config(text=f"等待对手落子... ({current})")
    
    def _update_network_control_panel(self, state):
        """更新网络模式下的控制面板"""
        board = state.get('board')
        if not board:
            return
        
        # 获取玩家信息（用户名）
        players = state.get('players', {})
        black_name = players.get('black', '等待中...')
        white_name = players.get('white', '等待中...')
        
        # 显示用户名
        my_color = state.get('my_color')
        
        # 使用 self.current_user
        if my_color == 'black' and self.current_user:
            black_display = f"{self.current_user.username} (你)"
        else:
            black_display = black_name or '等待中...'
        
        if my_color == 'white' and self.current_user:
            white_display = f"{self.current_user.username} (你)"
        else:
            white_display = white_name or '等待中...'
        
        # 使用正确的标签名 black_info_label / white_info_label
        self.control_panel.black_info_label.config(text=f"黑方: {black_display}")
        self.control_panel.white_info_label.config(text=f"白方: {white_display}")
        
        # 更新游戏类型
        game_type = state.get('game_type', '')
        game_type_names = {'gomoku': '五子棋', 'go': '围棋', 'othello': '黑白棋'}
        self.control_panel.game_type_label.config(text=f"游戏类型: {game_type_names.get(game_type, '-')}")
        
        # 更新当前回合
        if state.get('game_over'):
            winner = state.get('winner')
            if winner == 'draw':
                self.control_panel.player_label.config(text="游戏结束: 平局")
            else:
                winner_name = "黑方" if winner == 'black' else "白方"
                self.control_panel.player_label.config(text=f"获胜方: {winner_name}")
        else:
            current = "黑方" if state.get('current_player') == 'black' else "白方"
            is_my_turn = state.get('is_my_turn', False)
            turn_text = f"当前回合: {current}"
            if is_my_turn:
                turn_text += " (你)"
            self.control_panel.player_label.config(text=turn_text)
        
        # 更新比分（统计棋子数）
        black_count = 0
        white_count = 0
        for i in range(board.size):
            for j in range(board.size):
                stone = board.get_stone(i, j)
                if stone == 'black':
                    black_count += 1
                elif stone == 'white':
                    white_count += 1
        
        self.control_panel.score_label.config(text=f"比分: 黑{black_count} - 白{white_count}")
        self.control_panel.move_count_label.config(text=f"落子数: {black_count + white_count}")
        self.control_panel.undo_label.config(text="悔棋次数: 需对方同意")
    
    def _on_network_game_start(self, data):
        """网络游戏开始回调"""
        self.window.after(0, self._setup_network_game, data)
    
    def _setup_network_game(self, data):
        """设置网络游戏"""
        board_size = data.get('board_size', 15)
        self._create_canvas(board_size)
        self.control_panel.clear_history()
        messagebox.showinfo("游戏开始", f"游戏已开始！你是{self.network_client.color}方")
    
    def _on_network_game_over(self, data):
        """网络游戏结束回调"""
        def show_result():
            winner = data.get('winner')
            my_color = self.network_client.color if self.network_client else None
            
            # 更新当前用户的战绩
            if self.current_user and winner and winner != 'draw':
                won = (winner == my_color)
                self.platform.user_manager.update_user_stats(self.current_user.username, won)
                # 刷新用户信息
                self.current_user = self.platform.user_manager.get_user(self.current_user.username)
                self.control_panel.update_user_display(self.current_user)
            
            # 显示结果
            if winner == 'draw':
                message = "游戏结束\n\n平局！"
            elif winner == my_color:
                message = "🎉 游戏结束\n\n恭喜你获胜！"
            else:
                winner_name = "黑方" if winner == 'black' else "白方"
                message = f"游戏结束\n\n{winner_name}获胜！"
            
            messagebox.showinfo("游戏结束", message)
        
        self.window.after(0, show_result)
    
    def _on_network_undo_request(self, data):
        """收到悔棋请求"""
        def handle():
            from_user = data.get('from', '对方')
            result = messagebox.askyesno("悔棋请求", f"{from_user} 请求悔棋，是否同意？")
            if self.network_client:
                self.network_client.respond_undo(result)
                if result:
                    self.status_bar.config(text="已同意悔棋")
                else:
                    self.status_bar.config(text="已拒绝悔棋")
        
        self.window.after(0, handle)

    def run(self):
        """运行GUI"""
        self.window.mainloop()


def main():
    gui = GameGUI()
    gui.run()


if __name__ == '__main__':
    main()