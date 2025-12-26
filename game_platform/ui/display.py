# game_platform/ui/display.py
"""
显示组件
设计模式：组合模式、建造者模式
"""

from abc import ABC, abstractmethod


class DisplayComponent(ABC):
    """显示组件基类"""
    
    @abstractmethod
    def render(self, **kwargs):
        """渲染组件"""
        pass


class BoardDisplay(DisplayComponent):
    """棋盘显示"""
    
    # 棋子符号
    STONES = {
        None: '·',
        'black': '●',
        'white': '○'
    }
    
    def render(self, board=None, **kwargs):
        """渲染棋盘"""
        if board is None:
            return "没有正在进行的游戏"
        
        lines = []
        size = board.size
        
        # 列标题
        col_labels = '    ' + ' '.join(
            chr(ord('A') + i) for i in range(size)
        )
        lines.append(col_labels)
        lines.append('  ┌' + '─' * (size * 2 + 1) + '┐')
        
        # 棋盘内容
        for i in range(size):
            row_label = f'{i+1:2d}'
            row_content = ' '.join(
                self.STONES[board.grid[i][j]] for j in range(size)
            )
            lines.append(f'{row_label}│ {row_content} │')
        
        lines.append('  └' + '─' * (size * 2 + 1) + '┘')
        
        return '\n'.join(lines)


class StatusDisplay(DisplayComponent):
    """状态显示"""
    
    def render(self, game_state=None, **kwargs):
        """渲染游戏状态"""
        if game_state is None:
            return ""
        
        lines = []
        lines.append("=" * 40)
        
        # 玩家信息
        black_player = game_state.get('black_player')
        white_player = game_state.get('white_player')
        
        black_name = self._get_player_display(black_player)
        white_name = self._get_player_display(white_player)
        
        lines.append(f"黑方(●): {black_name}")
        lines.append(f"白方(○): {white_name}")
        lines.append("-" * 40)
        
        # 当前状态
        if game_state.get('replay_mode'):
            step = game_state.get('replay_step', 0)
            total = game_state.get('replay_total', 0)
            lines.append(f"[回放模式] 步骤: {step}/{total}")
        elif game_state['game_over']:
            winner = game_state['winner']
            if winner == 'draw':
                lines.append("游戏结束: 平局")
            else:
                winner_name = "黑方" if winner == 'black' else "白方"
                lines.append(f"游戏结束: {winner_name}获胜!")
            
            # 显示最终分数（如果有）
            if 'final_score' in game_state:
                score = game_state['final_score']
                lines.append(f"最终比分 - 黑: {score['black']}, 白: {score['white']}")
        else:
            current = "黑方" if game_state['current_player'] == 'black' else "白方"
            lines.append(f"当前回合: {current}")
            
            undo_info = f"悔棋次数: {game_state['undo_count']}/{game_state['max_undo_count']}"
            lines.append(undo_info)
        
        lines.append("=" * 40)
        
        return '\n'.join(lines)
    
    def _get_player_display(self, player):
        """获取玩家显示名称"""
        if player is None:
            return "游客"
        return player.get_display_name()


class HelpDisplay(DisplayComponent):
    """帮助信息显示"""
    
    def __init__(self):
        self.visible = True
    
    def toggle(self):
        """切换显示状态"""
        self.visible = not self.visible
    
    def render(self, **kwargs):
        """渲染帮助信息"""
        if not self.visible:
            return ""
        
        return """
可用命令:
  start <type> <size> - 开始游戏 (type: gomoku/go/othello)
  move <row> <col>    - 落子
  pass                - 弃权
  undo                - 悔棋
  resign              - 认输
  reset               - 重新开始
  save <file>         - 保存游戏
  load <file>         - 加载游戏
  help                - 显示/隐藏帮助
  quit                - 退出
"""


class MessageDisplay(DisplayComponent):
    """消息显示"""
    
    # 消息类型样式
    STYLES = {
        'info': '[信息]',
        'success': '[成功]',
        'error': '[错误]',
        'warning': '[警告]'
    }
    
    def render(self, message="", msg_type='info', **kwargs):
        """渲染消息"""
        prefix = self.STYLES.get(msg_type, '[信息]')
        return f"{prefix} {message}"


class CompositeDisplay(DisplayComponent):
    """组合显示组件"""
    
    def __init__(self):
        self.components = []
    
    def add(self, component):
        """添加子组件"""
        self.components.append(component)
    
    def remove(self, component):
        """移除子组件"""
        self.components.remove(component)
    
    def render(self, **kwargs):
        """渲染所有子组件"""
        outputs = []
        for component in self.components:
            output = component.render(**kwargs)
            if output:
                outputs.append(output)
        return '\n'.join(outputs)


class DisplayBuilder:
    """显示建造者
    设计模式：建造者模式
    """
    
    def __init__(self):
        self.display = CompositeDisplay()
    
    def add_component(self, component):
        """添加组件"""
        self.display.add(component)
        return self
    
    def build(self):
        """构建最终显示"""
        return self.display