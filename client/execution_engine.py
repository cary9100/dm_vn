# 文件名: client/execution_engine.py
# 客户端执行引擎模块
# 职责：连接服务器WebSocket，接收交易信号，并转换为本地交易指令

import json
import logging
import asyncio
import websockets
from typing import Optional, Callable
from threading import Thread

# 配置日志
logger = logging.getLogger('Execution Engine')


class ExecutionEngine:
    """
    客户端执行引擎，负责接收服务器信号并执行交易
    """

    def __init__(self, server_url: str = "ws://localhost:8765"):
        """
        初始化执行引擎
        :param server_url: 服务器WebSocket地址
        """
        self.server_url = server_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        self.signal_handler: Optional[Callable] = None
        logger.info(f"执行引擎初始化完成，将连接服务器: {server_url}")

    def set_signal_handler(self, handler: Callable):
        """
        设置信号处理回调函数
        :param handler: 处理接收到的交易信号的函数
        """
        self.signal_handler = handler
        logger.info("信号处理器设置完成")

    async def connect(self):
        """
        连接服务器WebSocket
        """
        try:
            logger.info(f"正在连接服务器: {self.server_url}")
            self.websocket = await websockets.connect(self.server_url)
            self.running = True
            logger.info("服务器连接成功!")

            # 发送客户端身份信息（未来可扩展为认证信息）
            client_info = {
                "client_id": "test_client_001",
                "client_type": "veighna_trader",
                "version": "1.0.0"
            }
            await self.websocket.send(json.dumps(client_info))

        except Exception as e:
            logger.error(f"连接服务器失败: {e}")
            self.running = False
            raise

    async def listen(self):
        """
        监听服务器消息
        """
        if not self.websocket:
            logger.error("WebSocket连接未建立，无法监听消息")
            return

        try:
            logger.info("开始监听服务器信号...")
            async for message in self.websocket:
                await self._process_message(message)

        except websockets.exceptions.ConnectionClosed:
            logger.warning("服务器连接已关闭")
        except Exception as e:
            logger.error(f"监听消息时发生错误: {e}")
        finally:
            self.running = False

    async def _process_message(self, message: str):
        """
        处理接收到的消息
        :param message: 原始消息字符串
        """
        try:
            # 解析JSON消息
            signal_data = json.loads(message)
            logger.info(f"接收到交易信号: {signal_data}")

            # 如果有设置信号处理器，则调用它处理信号
            if self.signal_handler:
                self.signal_handler(signal_data)
            else:
                logger.warning("接收到信号，但未设置信号处理器")
                # 默认处理：打印信号信息
                self._default_signal_handler(signal_data)

        except json.JSONDecodeError:
            logger.error(f"接收到的消息不是有效的JSON格式: {message}")
        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}")

    def _default_signal_handler(self, signal_data: dict):
        """
        默认信号处理器
        :param signal_data: 信号数据字典
        """
        action = signal_data.get('action', 'UNKNOWN')
        symbol = signal_data.get('symbol', 'UNKNOWN')
        price = signal_data.get('price', 0)
        volume = signal_data.get('volume', 0)

        print(f"=== 接收到交易信号 ===")
        print(f"操作: {action}")
        print(f"标的: {symbol}")
        print(f"价格: {price}")
        print(f"数量: {volume}")
        print(f"====================")

        # 这里未来会转换为VeighNa的交易指令并执行
        logger.info(f"信号已接收，待转换为交易指令: {action} {symbol} {volume}@${price}")

    async def run(self):
        """
        运行执行引擎（连接服务器并开始监听）
        """
        try:
            await self.connect()
            await self.listen()
        except Exception as e:
            logger.error(f"执行引擎运行失败: {e}")
        finally:
            await self.close()

    async def close(self):
        """
        关闭连接
        """
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket连接已关闭")
        self.running = False

    def start_in_thread(self):
        """
        在新线程中启动执行引擎（便于集成到VeighNa）
        """

        def run_engine():
            asyncio.run(self.run())

        self.thread = Thread(target=run_engine, daemon=True)
        self.thread.start()
        logger.info("执行引擎已在后台线程中启动")


# 测试函数
async def main_test():
    """测试执行引擎"""
    print("开始测试执行引擎...")
    engine = ExecutionEngine()

    try:
        # 运行引擎（会阻塞直到连接关闭）
        await engine.run()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    finally:
        print("测试结束")


if __name__ == "__main__":
    # 配置日志输出到控制台
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行测试
    asyncio.run(main_test())