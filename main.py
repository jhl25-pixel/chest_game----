# main.py
"""
棋类对战平台主入口
"""

import sys


def main():
    """主函数 - 直接启动GUI"""
    try:
        from game_platform.ui.gui import GameGUI
        gui = GameGUI()
        gui.run()
    except ImportError as e:
        print(f"启动失败: {e}")
        print("请确保已正确安装所有依赖")
        sys.exit(1)


if __name__ == '__main__':
    main()