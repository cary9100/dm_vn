# 文件名: server/websocket_server.py
# WebSocket 服务器模块
# 职责：启动一个WebSocket服务器，处理客户端的连接、断开、消息接收和信号广播

import asyncio
import json
import logging
from typing import Set
import websockets
from websockets.server import WebSocketServerProtocol

# 配置日志
logger = logging.getLogger('WebSocket Server')

class WebSocketServer:
    """
    WebSocket 服务器类，管理所有客户端连接和消息广播。
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        初始化WebSocket服务器
        :param host: 绑定主机地址
        :param port: 绑定端口号
        """
        self.host = host
        self.port = port
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        logger.info(f"WebSocket服务器初始化完成，将运行在 ws://{self.host}:{self.port}")

    async def handler(self, websocket: WebSocketServerProtocol):
        """
        处理每个客户端连接的协程（coroutine）。
        :param websocket: 客户端连接对象
        """
        # 注册新客户端
        self.connected_clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"新的客户端连接成功! 客户端ID: {client_id}。当前连接数: {len(self.connected_clients)}")

        try:
            # 保持连接活跃，并监听来自该客户端的任何消息
            async for message in websocket:
                # 目前我们先简单打印和记录任何从客户端发来的消息
                logger.info(f"收到来自客户端 {client_id} 的消息: {message}")
                # 这里未来可以添加消息处理逻辑（如：客户端认证、特定指令等）

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"客户端 {client_id} 连接断开。")
        finally:
            # 无论发生什么，确保连接被移除
            self.connected_clients.remove(websocket)
            logger.info(f"客户端 {client_id} 已从连接池移除。当前连接数: {len(self.connected_clients)}")

    async def broadcast_signal(self, signal_data: dict):
        """
        向所有已连接的客户端广播一个交易信号。
        这是服务端最重要的方法之一。
        :param signal_data: 要广播的信号数据（字典格式）
        """
        if not self.connected_clients:
            logger.warning("尝试广播信号，但没有客户端连接。")
            return

        # 将信号数据转换为JSON字符串
        message = json.dumps(signal_data)
        logger.info(f"准备广播信号: {message}")

        # 创建广播给所有客户端的任务列表
        tasks = []
        for client in self.connected_clients:
            # 为每个客户端创建一个发送消息的任务
            task = asyncio.create_task(client.send(message))
            tasks.append(task)

        # 等待所有发送任务完成
        if tasks:
            await asyncio.gather(*tasks)
            logger.info(f"信号已成功广播给 {len(self.connected_clients)} 个客户端。")

    async def start_server(self):
        """
        启动WebSocket服务器。
        这是一个异步协程，需要在事件循环中运行。
        """
        logger.info("正在启动WebSocket服务器...")
        # 创建并启动服务器
        self.server = await websockets.serve(self.handler, self.host, self.port)
        logger.info(f"WebSocket服务器已在 ws://{self.host}:{self.port} 上启动成功!")

    async def stop_server(self):
        """
        停止WebSocket服务器。
        """
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket服务器已停止。")


# 简单的测试函数
async def main_test():
    """一个简单的测试函数，用于验证WebSocket服务器是否能独立工作"""
    print("启动WebSocket服务器测试...")
    ws_server = WebSocketServer()

    try:
        # 启动服务器
        await ws_server.start_server()
        print("服务器已启动。按 Ctrl+C 停止测试。")

        # 模拟：等待一段时间，然后广播一个测试信号
        await asyncio.sleep(2)
        test_signal = {
            "action": "BUY",
            "symbol": "000001.SH",
            "price": 3200.50,
            "volume": 100,
            "timestamp": "2025-09-08 10:00:00",
            "strategy_id": "test_strategy_001"
        }
        await ws_server.broadcast_signal(test_signal)

        # 让服务器保持运行一段时间
        await asyncio.sleep(10)

    except asyncio.CancelledError:
        print("\n测试被中断。")
    finally:
        await ws_server.stop_server()
        print("测试结束。")


# 如果是直接运行此脚本，则执行测试
if __name__ == "__main__":
    asyncio.run(main_test())