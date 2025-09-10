# 文件名: server/main_engine.py
# 服务端主引擎模块
# 职责：整合和管理服务端的核心组件，是服务端的“大脑”

import logging
from typing import Any, Optional

# 配置日志格式，方便我们查看运行状态和调试
logging.basicConfig(
    level=logging.INFO,  # 设置日志级别为 INFO，只记录重要信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
import asyncio
import threading
from typing import Optional
from server.websocket_server import WebSocketServer
# 创建一个logger对象，用于在本模块中记录日志
logger = logging.getLogger('Server Engine')


class ServerEngine:
    def __init__(self) -> None:
        logger.info("开始初始化服务端主引擎...")
        self.active: bool = False
        self.modules = {}
        self.stop_event = threading.Event()

        # 新增：初始化WebSocket服务器模块
        self.ws_server: Optional[WebSocketServer] = WebSocketServer()
        self.ws_server_task: Optional[asyncio.Task] = None

        # 新增：用于保存异步线程的事件循环
        self.async_loop = None

        logger.info("服务端主引擎初始化完成.")

    def start(self) -> None:
        if self.active:
            logger.warning("引擎已经处于运行状态，无需重复启动。")
            return

        logger.info("正在启动服务端主引擎...")

        # 新增：在单独的线程中启动异步事件循环和WebSocket服务器
        self._start_async_components()

        self.active = True
        logger.info("服务端主引擎启动成功！")

    def _start_async_components(self):
        """启动需要运行在asyncio事件循环中的组件（如WebSocket服务器）"""

        def run_async_in_thread():
            # 创建一个新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 将事件循环保存到实例变量中，以便其他线程使用
            self.async_loop = loop

            try:
                # 启动WebSocket服务器
                loop.run_until_complete(self.ws_server.start_server())
                # 保持事件循环运行，直到收到停止信号
                loop.run_forever()
            except Exception as e:
                logger.error(f"异步组件运行错误: {e}")
            finally:
                # 清理工作
                tasks = asyncio.all_tasks(loop)
                for task in tasks:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
                logger.info("异步事件循环已关闭。")

        # 在新线程中运行异步事件循环
        self.async_thread = threading.Thread(target=run_async_in_thread, daemon=True)
        self.async_thread.start()
        logger.info("异步组件（WebSocket服务器）线程已启动。")

    def stop(self) -> None:
        if not self.active:
            logger.warning("引擎未在运行，无需停止。")
            return

        logger.info("正在停止服务端主引擎...")
        # 这里未来会安全地停止所有模块

        # 新增：停止异步事件循环（通过设置停止事件，在线程内部处理）
        # 由于WebSocket服务器运行在daemon线程中，主线程退出时它会自动被终止
        # 更优雅的关闭方式我们后续再实现
        self.active = False
        logger.info("服务端主引擎已停止。")

    async def broadcast_signal(self, signal_data: dict):
        """
        对外提供的广播信号方法。
        :param signal_data: 信号数据字典
        """
        if self.ws_server:
            await self.ws_server.broadcast_signal(signal_data)
        else:
            logger.error("尝试广播信号，但WebSocket服务器未初始化!")
    def broadcast_signal_sync(self, signal_data: dict):
        """
        同步方法：向所有客户端广播信号。
        该方法可以在任何线程中调用，它会将广播任务提交到异步线程的事件循环中。
        :param signal_data: 信号数据字典
        """
        if self.async_loop is None:
            logger.error("事件循环还未就绪，无法广播信号。")
            return

        # 使用run_coroutine_threadsafe来在事件循环中安全地运行协程
        future = asyncio.run_coroutine_threadsafe(self.broadcast_signal(signal_data), self.async_loop)
        try:
            # 等待协程完成，设置超时时间
            future.result(timeout=5.0)
        except asyncio.TimeoutError:
            logger.error("广播信号超时。")
        except Exception as e:
            logger.error(f"广播信号时发生错误: {e}")

    def write_log(self, msg: str) -> None:
        logger.info(msg)

# 以下代码用于简单的功能测试
if __name__ == "__main__":
    """
    如果直接运行这个python文件（而不是被导入），则执行下面的代码。
    这是一个非常好的‘写一步，测试一步’的习惯！
    """
    print("正在进行服务端主引擎的简单测试...")
    engine = ServerEngine()  # 初始化引擎
    engine.start()           # 启动引擎
    engine.write_log("这是一条测试日志信息。")  # 测试日志功能
    engine.stop()            # 停止引擎
    print("简单测试完成！")