# 文件名: server/run_server.py
# 服务端启动入口脚本 - 使用控制台输入作为停止信号的替代方案
import json
import sys
import os
import logging
import threading
import asyncio

# 配置日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Server App')

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from server.main_engine import ServerEngine


def console_listener(stop_event, engine):  # 修改函数签名，添加engine参数
    """
    在一个单独的线程中运行，监听控制台输入
    """
    while not stop_event.is_set():
        try:
            # 等待用户输入
            command = input().strip().lower()
            if command == 'exit' or command == 'quit':
                print("接收到退出命令，开始关闭服务器...")
                stop_event.set()
                break
            elif command == 'help':
                print("可用命令: exit/quit - 关闭服务器, help - 显示帮助, test_signal - 广播测试信号")
            elif command == 'test_signal':
                # 创建测试信号
                test_signal = {
                    "action": "BUY",
                    "symbol": "000001.SZ",  # 平安银行，深圳证券交易所
                    "price": 15.80,
                    "volume": 100,
                    "timestamp": "2025-09-08 14:30:00",
                    "strategy_id": "test_strategy_001",
                    "signal_id": "test_signal_001"
                }
                print(f"正在广播测试信号: {json.dumps(test_signal, indent=2)}")

                # 使用asyncio.run_coroutine_threadsafe来在正确的事件循环中执行异步函数
                # 由于WebSocket服务器运行在另一个线程的事件循环中，我们需要这种方式来调用
                if hasattr(engine, 'async_loop') and engine.async_loop:
                    future = asyncio.run_coroutine_threadsafe(
                        engine.broadcast_signal(test_signal),
                        engine.async_loop
                    )
                    # 等待异步操作完成或超时
                    try:
                        future.result(timeout=5.0)
                        print("测试信号广播成功!")
                    except asyncio.TimeoutError:
                        print("广播信号超时!")
                    except Exception as e:
                        print(f"广播信号时发生错误: {e}")
                else:
                    print("错误: 异步事件循环未就绪，无法广播信号。")
            else:
                print(f"未知命令: {command}. 输入 'help' 查看可用命令。")
        except (EOFError, KeyboardInterrupt):
            # 当输入流关闭或尝试Ctrl+C时也会触发
            stop_event.set()
            break

def main():
    print("=" * 50)
    print("Quant Trade System - 服务端启动中...")
    print("=" * 50)
    print("输入 'exit' 或 'quit' 并按回车来停止服务器。")
    print("输入 'help' 查看可用命令。")
    print("输入 'test_signal' 广播一个测试信号。")  # 新增提示

    engine = ServerEngine()
    stop_event = threading.Event()

    try:
        # console_thread = threading.Thread(target=console_listener, args=(stop_event,), daemon=True)
        # 修改：将engine传递给console_listener
        console_thread = threading.Thread(target=console_listener, args=(stop_event, engine), daemon=True)
        console_thread.start()

        engine.start()
        print("\n服务端已成功启动并运行。")
        logger.info("服务端主程序进入运行状态。")

        # 主循环
        while not stop_event.is_set():
            stop_event.wait(0.5)

    except Exception as e:
        logger.error(f"服务端运行发生错误: {e}", exc_info=True)
    finally:
        print("正在关闭服务端，请稍候...")
        engine.stop()
        stop_event.set()
        print("服务端已安全关闭。")
        logger.info("服务端应用程序已退出。")


if __name__ == "__main__":
    main()