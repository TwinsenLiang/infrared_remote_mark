#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import random

class InfraredReceiver:
    """红外接收器模拟类"""

    def __init__(self):
        # 用于去重的变量（针对所有遥控器统一去重）
        self.last_scancode = None
        self.last_signal_time = 0
        self.duplicate_threshold = 0.15  # 150ms内的相同信号视为重复

    def simulate_signal(self, button=None):
        """模拟接收红外信号（用于测试）"""
        # 生成随机信号用于测试
        signal = f"0x{random.randint(0x87EE0000, 0x87EEFFFF):08X}"

        return {
            "signal": signal,
            "timestamp": time.time(),
            "button": button if button else "unknown"
        }
    
    def wait_for_signal(self, timeout=5.0):
        """等待接收红外信号（直接读取input设备）"""
        import struct
        import select
        import time

        IR_DEVICE = "/dev/input/event1"  # GPIO红外接收器设备

        try:
            # 打开红外设备
            with open(IR_DEVICE, 'rb') as device:
                start_time = time.time()

                # 等待事件
                while time.time() - start_time < timeout:
                    # 使用 select 检查是否有数据
                    ready = select.select([device], [], [], 0.5)

                    if ready[0]:
                        # 读取输入事件
                        # struct input_event 格式: long, long, unsigned short, unsigned short, int
                        # timeval.tv_sec, timeval.tv_usec, type, code, value
                        event_data = device.read(24)  # input_event 结构大小

                        if len(event_data) == 24:
                            # 解包事件数据
                            tv_sec, tv_usec, ev_type, ev_code, ev_value = struct.unpack('llHHi', event_data)

                            # EV_MSC = 4, MSC_SCAN = 4 表示扫描码事件（红外信号）
                            if ev_type == 4 and ev_code == 4:  # MSC_SCAN 扫描码事件
                                # ev_value 是红外扫描码
                                scancode = ev_value

                                # 处理负数扫描码（将其转换为无符号整数）
                                if scancode < 0:
                                    scancode = scancode & 0xFFFFFFFF

                                current_time = time.time()

                                # 去重检查：统一对所有信号去重
                                if (self.last_scancode == scancode and
                                    current_time - self.last_signal_time < self.duplicate_threshold):
                                    # 这是重复信号，跳过并继续等待下一个
                                    continue

                                # 记录这次信号
                                self.last_scancode = scancode
                                self.last_signal_time = current_time

                                # 返回信号时不带协议信息，由前端自己决定
                                result = {
                                    "signal": f"0x{scancode:08X}",
                                    "timestamp": current_time,
                                    "button": f"IR_{scancode:08X}",
                                    "scancode": scancode
                                }
                                return result

            # 超时
            return {
                "error": "timeout",
                "message": "未接收到红外信号",
                "timeout": timeout
            }

        except FileNotFoundError:
            return {
                "error": "device_not_found",
                "message": f"红外设备未找到: {IR_DEVICE}"
            }
        except PermissionError:
            return {
                "error": "permission_denied",
                "message": f"无权限访问: {IR_DEVICE}。请确保有读取权限。"
            }
        except Exception as e:
            return {
                "error": "exception",
                "message": f"接收红外信号时出错: {str(e)}"
            }

# 全局红外接收器实例
ir_receiver = InfraredReceiver()

if __name__ == "__main__":
    # 测试代码
    print("红外接收器测试:")
    print("等待接收红外信号...")
    result = ir_receiver.wait_for_signal(timeout=10)
    print(f"接收结果: {result}")