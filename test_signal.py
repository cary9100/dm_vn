# test_signal.py
# 这个脚本用于测试PyCharm环境中Ctrl+C的基本行为
import time
import signal
import sys

def signal_handler(sig, frame):
    print('!!! 明确接收到Ctrl+C信号 !!!')
    sys.exit(0)

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)

print("测试脚本启动。请按 Ctrl+C 来测试信号捕获。")
print("如果这个脚本能正常响应Ctrl+C，说明问题在我们的服务器代码中。")
print("如果这个脚本也不能响应，可能是PyCharm或环境配置问题。")

# 简单的等待循环
while True:
    time.sleep(1)
    print("程序仍在运行...", end='\r')  # 使用\r让输出在同一行刷新