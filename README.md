# 棋类对战平台 v2.0

一个支持五子棋、围棋、黑白棋的综合对战平台，具备人机对战、网络对战、录像回放等功能。

## 功能特性

### 游戏类型
- ⚫ **五子棋 (Gomoku)**: 15×15棋盘，五连获胜
- ⚪ **围棋 (Go)**: 支持9×9, 13×13, 19×19棋盘
- 🔲 **黑白棋 (Othello)**: 8×8棋盘，翻转对手棋子

### AI系统
- **Level 1**: 随机落子AI
- **Level 2**: 评估函数AI（位置权重+棋型识别）
- **Level 3**: Alpha-Beta剪枝搜索AI（优先级检测+深度搜索）

### 用户系统
- 账户注册/登录
- 战绩统计（胜场/场次/胜率）
- 排行榜

### 其他功能
- 游戏存档/加载
- 录像保存/回放
- 网络对战（局域网TCP/IP）
- 悔棋、弃权、认输

## 快速开始

```bash
# 克隆项目
git clone <repository-url>
cd chess_game

# 运行游戏
python main.py
```

## 项目结构

```
game_platform/
├── board.py         # 棋盘类
├── game.py          # 游戏逻辑类
├── player.py        # 玩家类
├── platform.py      # 平台外观类
├── user.py          # 用户管理
├── replay.py        # 录像回放
├── ai/              # AI算法
│   ├── random_ai.py
│   ├── eval_ai.py
│   └── mcts_ai.py
├── network/         # 网络对战
│   ├── server.py
│   └── client.py
└── ui/
    └── gui.py       # 图形界面
```

## 设计模式

| 模式 | 应用 |
|-----|------|
| 工厂模式 | GameFactory, AIFactory, PlayerFactory |
| 策略模式 | AIStrategy接口及实现 |
| 外观模式 | GamePlatform统一接口 |
| 单例模式 | UserManager |
| 观察者模式 | 网络状态回调 |


## 文档

- [设计文档](面向对象第二阶段_设计文档.md) - 详细设计说明

## 技术栈

- Python 3.8+
- Tkinter (GUI)
- Socket (网络通信)
- JSON (数据存储)

## License

MIT License
