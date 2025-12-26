from game_platform.platform import GamePlatform
from game_platform.ui.display import (
    BoardDisplay, StatusDisplay, HelpDisplay, 
    MessageDisplay, DisplayBuilder
)


class GameClient:
    """游戏客户端"""
    
    def __init__(self):
        self.platform = GamePlatform()
        self.board_display = BoardDisplay()
        self.status_display = StatusDisplay()
        self.help_display = HelpDisplay()
        self.message_display = MessageDisplay()
        self.running = False
        
        self.current_black_user = None
        self.current_white_user = None
        
    def start(self):
        """启动客户端"""
        self.running = True
        print("=" * 50)
        print("      欢迎来到棋类对战平台！")
        print("=" * 50)
        print("\n支持游戏类型: gomoku(五子棋), go(围棋), othello(黑白棋)")
        print("支持对战模式: 玩家-玩家, 玩家-AI, AI-AI")
        print("\n输入 'help' 查看所有命令")
        
        while self.running:
            try:
                command = input("\n请输入命令: ").strip()
                if not command:
                    continue
                self.process_command(command)
            except KeyboardInterrupt:
                print("\n\n游戏已退出")
                break
            except Exception as e:
                print(self.message_display.render(f"未知错误: {str(e)}", 'error'))
                
    def process_command(self, command):
        """处理命令"""
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        
        try:
            if cmd == 'start':
                self.handle_start(parts)
            elif cmd == 'move':
                self.handle_move(parts)
            elif cmd == 'pass':
                self.handle_pass()
            elif cmd == 'undo':
                self.handle_undo()
            elif cmd == 'resign':
                self.handle_resign()
            elif cmd == 'reset':
                self.handle_reset(parts)
            elif cmd == 'save':
                self.handle_save(parts)
            elif cmd == 'load':
                self.handle_load(parts)
            elif cmd == 'register':
                self.handle_register(parts)
            elif cmd == 'login':
                self.handle_login(parts)
            elif cmd == 'logout':
                self.handle_logout(parts)
            elif cmd == 'leaderboard':
                self.handle_leaderboard()
            elif cmd == 'whoami':
                self.handle_whoami()
            elif cmd == 'savereplay':
                self.handle_save_replay(parts)
            elif cmd == 'replay':
                self.handle_replay(parts)
            elif cmd == 'next':
                self.handle_replay_next()
            elif cmd == 'prev':
                self.handle_replay_prev()
            elif cmd == 'goto':
                self.handle_replay_goto(parts)
            elif cmd == 'exitreplay':
                self.handle_exit_replay()
            elif cmd == 'help':
                self.handle_help()
            elif cmd == 'quit':
                self.handle_quit()
            else:
                print(self.message_display.render("未知命令，请输入 'help' 查看可用命令", 'error'))
        except ValueError as e:
            print(self.message_display.render(str(e), 'error'))
        except Exception as e:
            print(self.message_display.render(f"命令执行失败: {str(e)}", 'error'))
    
    def handle_start(self, parts):
        """处理开始游戏命令"""
        if len(parts) < 3:
            print(self.message_display.render(
                "用法: start <game_type> <size> [black_type] [white_type] [black_ai_level] [white_ai_level]\n"
                "  game_type: gomoku, go, othello\n"
                "  player_type: human, ai\n"
                "  ai_level: 1-3",
                'error'))
            return
        
        game_type = parts[1].lower()
        try:
            board_size = int(parts[2])
        except ValueError:
            print(self.message_display.render("棋盘大小必须是整数", 'error'))
            return
        
        black_type = parts[3].lower() if len(parts) > 3 else 'human'
        white_type = parts[4].lower() if len(parts) > 4 else 'human'
        black_ai_level = int(parts[5]) if len(parts) > 5 else 1
        white_ai_level = int(parts[6]) if len(parts) > 6 else 1
        
        self.platform.create_game(
            game_type, board_size,
            black_type, white_type,
            black_ai_level, white_ai_level,
            self.current_black_user, self.current_white_user
        )
        
        game_names = {'gomoku': '五子棋', 'go': '围棋', 'othello': '黑白棋'}
        game_name = game_names.get(game_type, game_type)
        print(self.message_display.render(
            f"已开始 {game_name} 游戏，棋盘大小: {board_size}x{board_size}", 'success'))
        self.display_game()
        
    def handle_move(self, parts):
        """处理落子命令"""
        if len(parts) != 3:
            print(self.message_display.render("用法: move <row> <col>", 'error'))
            return
        
        try:
            row = int(parts[1]) - 1
            col_str = parts[2].upper()
            col = ord(col_str[0]) - ord('A')
        except (ValueError, IndexError):
            print(self.message_display.render("位置格式错误", 'error'))
            return
        
        self.platform.make_move(row, col)
        print(self.message_display.render(f"落子成功: {parts[1]}{parts[2]}", 'success'))
        self.display_game()
        
    def handle_pass(self):
        """处理弃权命令"""
        self.platform.pass_move()
        print(self.message_display.render("弃权", 'success'))
        self.display_game()
        
    def handle_undo(self):
        """处理悔棋命令"""
        self.platform.undo_move()
        print(self.message_display.render("悔棋成功", 'success'))
        self.display_game()
        
    def handle_resign(self):
        """处理认输命令"""
        self.platform.resign()
        print(self.message_display.render("认输", 'success'))
        self.display_game()
        
    def handle_reset(self, parts):
        """处理重新开始命令"""
        board_size = None
        if len(parts) == 2:
            try:
                board_size = int(parts[1])
            except ValueError:
                print(self.message_display.render("棋盘大小必须是整数", 'error'))
                return
        
        self.platform.reset_game(board_size)
        print(self.message_display.render("游戏已重新开始", 'success'))
        self.display_game()
        
    def handle_save(self, parts):
        """处理保存命令"""
        if len(parts) != 2:
            print(self.message_display.render("用法: save <filename>", 'error'))
            return
        
        filename = parts[1]
        if not filename.endswith('.json'):
            filename += '.json'
        
        self.platform.save_to_file(filename)
        print(self.message_display.render(f"游戏已保存到 {filename}", 'success'))
        
    def handle_load(self, parts):
        """处理加载命令"""
        if len(parts) != 2:
            print(self.message_display.render("用法: load <filename>", 'error'))
            return
        
        filename = parts[1]
        if not filename.endswith('.json'):
            filename += '.json'
        
        self.platform.load_from_file(filename)
        print(self.message_display.render(f"游戏已从 {filename} 加载", 'success'))
        self.display_game()
    
    def handle_register(self, parts):
        """处理注册命令"""
        if len(parts) != 4:
            print(self.message_display.render(
                "用法: register <black/white> <username> <password>", 'error'))
            return
        
        color = parts[1].lower()
        username = parts[2]
        password = parts[3]
        
        if color not in ['black', 'white']:
            print(self.message_display.render("请指定 black 或 white", 'error'))
            return
        
        user = self.platform.register_user(username, password)
        
        if color == 'black':
            self.current_black_user = user
        else:
            self.current_white_user = user
        
        print(self.message_display.render(f"注册成功！{color}方用户: {username}", 'success'))
    
    def handle_login(self, parts):
        """处理登录命令"""
        if len(parts) != 4:
            print(self.message_display.render(
                "用法: login <black/white> <username> <password>", 'error'))
            return
        
        color = parts[1].lower()
        username = parts[2]
        password = parts[3]
        
        if color not in ['black', 'white']:
            print(self.message_display.render("请指定 black 或 white", 'error'))
            return
        
        user = self.platform.login_user(username, password)
        
        if color == 'black':
            self.current_black_user = user
        else:
            self.current_white_user = user
        
        print(self.message_display.render(f"登录成功！{color}方用户: {user}", 'success'))
    
    def handle_logout(self, parts):
        """处理登出命令"""
        if len(parts) != 2:
            print(self.message_display.render("用法: logout <black/white>", 'error'))
            return
        
        color = parts[1].lower()
        
        if color == 'black':
            self.current_black_user = None
            print(self.message_display.render("黑方已登出", 'success'))
        elif color == 'white':
            self.current_white_user = None
            print(self.message_display.render("白方已登出", 'success'))
        else:
            print(self.message_display.render("请指定 black 或 white", 'error'))
    
    def handle_leaderboard(self):
        """显示排行榜"""
        leaderboard = self.platform.get_leaderboard()
        
        print("\n" + "=" * 40)
        print("           排 行 榜")
        print("=" * 40)
        
        if not leaderboard:
            print("  暂无数据")
        else:
            for i, user in enumerate(leaderboard, 1):
                win_rate = user.get_win_rate() * 100
                print(f"  {i}. {user.username}: {user.wins}胜/{user.games}场 ({win_rate:.1f}%)")
        
        print("=" * 40)
    
    def handle_whoami(self):
        """显示当前登录用户"""
        print("\n当前用户:")
        print(f"  黑方: {self.current_black_user or '游客'}")
        print(f"  白方: {self.current_white_user or '游客'}")
    
    def handle_save_replay(self, parts):
        """保存录像"""
        if len(parts) != 2:
            print(self.message_display.render("用法: savereplay <filename>", 'error'))
            return
        
        filename = self.platform.save_replay(parts[1])
        print(self.message_display.render(f"录像已保存到 {filename}", 'success'))
    
    def handle_replay(self, parts):
        """加载并进入回放模式"""
        if len(parts) != 2:
            print(self.message_display.render("用法: replay <filename>", 'error'))
            return
        
        filename = parts[1]
        if not filename.endswith('.replay'):
            filename += '.replay'
        
        self.platform.load_replay(filename)
        print(self.message_display.render(f"已加载录像，进入回放模式", 'success'))
        
        metadata = self.platform.replayer.get_metadata()
        if metadata:
            print(f"\n游戏类型: {metadata.get('game_type')}")
            print(f"总步数: {metadata.get('total_moves')}")
            print(f"黑方: {metadata.get('black_player', {}).get('name', '未知')}")
            print(f"白方: {metadata.get('white_player', {}).get('name', '未知')}")
            print(f"胜者: {metadata.get('winner', '未结束')}")
        
        print("\n回放命令: next(下一步), prev(上一步), goto <n>(跳转), exitreplay(退出)")
        self.display_game()
    
    def handle_replay_next(self):
        """回放下一步"""
        record = self.platform.replay_next()
        if record:
            step = self.platform.replayer.get_current_step()
            total = self.platform.replayer.get_total_steps()
            print(self.message_display.render(f"步骤 {step}/{total}", 'success'))
            self.display_game()
        else:
            print(self.message_display.render("已到达录像末尾", 'error'))
    
    def handle_replay_prev(self):
        """回放上一步"""
        record = self.platform.replay_prev()
        if record:
            step = self.platform.replayer.get_current_step()
            total = self.platform.replayer.get_total_steps()
            print(self.message_display.render(f"步骤 {step}/{total}", 'success'))
            self.display_game()
        else:
            print(self.message_display.render("已到达录像开头", 'error'))
    
    def handle_replay_goto(self, parts):
        """回放跳转"""
        if len(parts) != 2:
            print(self.message_display.render("用法: goto <step>", 'error'))
            return
        
        try:
            step = int(parts[1])
        except ValueError:
            print(self.message_display.render("步数必须是整数", 'error'))
            return
        
        self.platform.replay_goto(step)
        step = self.platform.replayer.get_current_step()
        total = self.platform.replayer.get_total_steps()
        print(self.message_display.render(f"跳转到步骤 {step}/{total}", 'success'))
        self.display_game()
    
    def handle_exit_replay(self):
        """退出回放模式"""
        self.platform.exit_replay()
        print(self.message_display.render("已退出回放模式", 'success'))
        
    def handle_help(self):
        """处理帮助命令"""
        help_text = """
========== 游戏命令 ==========
start <type> <size> [black_type] [white_type] [black_ai] [white_ai]
                    - 开始游戏
                      type: gomoku/go/othello
                      player_type: human/ai
                      ai_level: 1(随机)/2(评估)/3(MCTS)
move <row> <col>    - 落子 (如: move 8 H)
pass                - 弃权 (围棋/黑白棋)
undo                - 悔棋
resign              - 认输
reset [size]        - 重新开始

========== 存档命令 ==========
save <filename>     - 保存游戏
load <filename>     - 加载游戏

========== 用户命令 ==========
register <color> <user> <pwd>  - 注册账号
login <color> <user> <pwd>     - 登录账号
logout <color>                 - 登出
leaderboard                    - 查看排行榜
whoami                         - 查看当前用户

========== 录像命令 ==========
savereplay <filename>  - 保存录像
replay <filename>      - 加载并回放录像
next                   - 回放下一步
prev                   - 回放上一步
goto <step>            - 跳转到指定步
exitreplay             - 退出回放模式

========== 其他命令 ==========
help                - 显示帮助
quit                - 退出游戏
"""
        print(help_text)
        
    def handle_quit(self):
        """处理退出命令"""
        self.running = False
        print(self.message_display.render("感谢使用，再见！", 'success'))
        
    def display_game(self):
        """显示游戏界面"""
        game_state = self.platform.get_game_state()
        if game_state is None:
            return
        
        builder = DisplayBuilder()
        builder.add_component(self.status_display)
        builder.add_component(self.board_display)
        
        display = builder.build()
        print("\n" + display.render(game_state=game_state, board=game_state['board']))


if __name__ == '__main__':
    client = GameClient()
    client.start()
