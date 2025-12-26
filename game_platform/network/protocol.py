# game_platform/network/protocol.py
"""
网络通信协议
"""

import json
from enum import Enum


class MessageType(Enum):
    """消息类型"""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    CREATE_GAME = "create_game"
    JOIN_GAME = "join_game"
    GAME_START = "game_start"
    GAME_OVER = "game_over"
    MOVE = "move"
    PASS = "pass"
    UNDO_REQUEST = "undo_request"
    UNDO_RESPONSE = "undo_response"
    RESIGN = "resign"
    SYNC_STATE = "sync_state"
    CHAT = "chat"
    ERROR = "error"
    OK = "ok"


class Protocol:
    """通信协议"""
    
    ENCODING = 'utf-8'
    DELIMITER = '\n'
    
    @staticmethod
    def encode(msg_type, data=None):
        """编码消息"""
        message = {
            'type': msg_type.value if isinstance(msg_type, MessageType) else msg_type,
            'data': data or {}
        }
        json_str = json.dumps(message, ensure_ascii=False)
        return (json_str + Protocol.DELIMITER).encode(Protocol.ENCODING)
    
    @staticmethod
    def decode(data):
        """解码消息"""
        try:
            if isinstance(data, bytes):
                data = data.decode(Protocol.ENCODING)
            
            messages = []
            for line in data.strip().split(Protocol.DELIMITER):
                if line:
                    message = json.loads(line)
                    msg_type = MessageType(message['type'])
                    msg_data = message.get('data', {})
                    messages.append((msg_type, msg_data))
            
            return messages
        except Exception as e:
            return [(MessageType.ERROR, {'error': str(e)})]