# 文件名: client/run.py
# VeighNa Trader 客户端主入口文件 - 集成执行引擎版本

import sys
import logging
from threading import Thread

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("vt_client.log"),  # 日志输出到文件
        logging.StreamHandler(sys.stdout)      # 日志输出到控制台
    ]
)

# 将当前目录添加到Python路径，以便导入自定义模块
sys.path.insert(0, "./")

# 导入VeighNa相关模块 - 使用正确的导入方式
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

# 交易接口 - 使用正确的导入方式
from vnpy_ctp import CtpGateway

# 功能应用 - 使用正确的导入方式
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_ctabacktester import CtaBacktesterApp
from vnpy_datamanager import DataManagerApp

# 导入我们自定义的执行引擎
from client.execution_engine import ExecutionEngine


def create_signal_handler(main_engine: MainEngine):
    """
    创建信号处理器，将接收到的信号转换为VeighNa交易指令

    :param main_engine: VeighNa主引擎实例
    :return: 信号处理函数
    """

    def handle_signal(signal_data: dict):
        """
        处理接收到的交易信号

        :param signal_data: 信号数据字典
        """
        # 记录接收到的信号
        logging.info(f"处理交易信号: {signal_data}")

        # 提取信号参数
        action = signal_data.get('action', '').upper()
        symbol = signal_data.get('symbol', '')
        price = signal_data.get('price', 0)
        volume = signal_data.get('volume', 0)
        strategy_id = signal_data.get('strategy_id', 'unknown')
        signal_id = signal_data.get('signal_id', 'unknown')

        # 打印信号信息
        print(f"\n=== 执行交易信号 ===")
        print(f"策略: {strategy_id}")
        print(f"信号ID: {signal_id}")
        print(f"操作: {action}")
        print(f"标的: {symbol}")
        print(f"价格: {price}")
        print(f"数量: {volume}")
        print(f"====================")

        # 这里未来将实现信号到VeighNa交易指令的转换
        # 例如: 创建OrderRequest对象并通过main_engine发送

        # 暂时只记录日志
        logging.info(f"信号待执行: {action} {symbol} {volume}@${price}")

        # TODO: 实现实际的交易指令发送逻辑
        # 示例代码:
        # if action == "BUY":
        #     order_req = OrderRequest(
        #         symbol=symbol,
        #         exchange=Exchange.SSE,  # 需要根据symbol确定交易所
        #         direction=Direction.LONG,
        #         type=OrderType.LIMIT,
        #         price=price,
        #         volume=volume,
        #         offset=Offset.OPEN
        #     )
        #     main_engine.send_order(order_req, "CTP")  # 假设使用CTP网关

    return handle_signal


def main():
    """主函数"""
    # 创建Qt应用
    qapp = create_qapp()

    # 创建事件引擎
    event_engine = EventEngine()

    # 创建主引擎
    main_engine = MainEngine(event_engine)

    # 添加交易接口
    main_engine.add_gateway(CtpGateway)

    # 添加功能应用
    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(CtaBacktesterApp)
    main_engine.add_app(DataManagerApp)

    # 创建主窗口
    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    # 创建并启动执行引擎
    logging.info("初始化执行引擎...")
    execution_engine = ExecutionEngine()

    # 设置信号处理器
    signal_handler = create_signal_handler(main_engine)
    execution_engine.set_signal_handler(signal_handler)

    # 在后台线程中启动执行引擎
    execution_engine.start_in_thread()
    logging.info("执行引擎已启动并在后台运行")

    # 运行Qt应用
    sys.exit(qapp.exec_())


if __name__ == "__main__":
    main()