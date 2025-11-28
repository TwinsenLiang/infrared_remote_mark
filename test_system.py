#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
from infrared_receiver import ir_receiver

def test_remote_app():
    """测试遥控器应用的功能"""
    base_url = "http://localhost:5000/api"
    
    print("==========================================")
    print("苹果A1294遥控器系统功能测试")
    print("==========================================")
    
    # 1. 测试获取SVG数据
    print("\n1. 测试SVG数据获取...")
    try:
        response = requests.get(f"{base_url}/svg_data")
        if response.status_code == 200:
            svg_data = response.json()
            print("✓ SVG数据获取成功")
            print(f"  SVG内容长度: {len(svg_data['svg'])} 字符")
        else:
            print("✗ SVG数据获取失败")
            return
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到服务器，请确保应用已启动")
        return
    
    # 2. 测试按键点击
    print("\n2. 测试按键点击...")
    button_tests = [
        {"name": "上键", "x": 132, "y": 120},
        {"name": "下键", "x": 131, "y": 316}, 
        {"name": "左键", "x": 34, "y": 217},
        {"name": "右键", "x": 229, "y": 218},
        {"name": "确认键", "x": 131, "y": 218},
        {"name": "菜单键", "x": 68, "y": 402},
        {"name": "播放暂停键", "x": 194, "y": 402}
    ]
    
    for button in button_tests:
        try:
            response = requests.post(
                f"{base_url}/button_click",
                json={"x": button["x"], "y": button["y"]}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("button"):
                    print(f"✓ {button['name']} 点击检测成功: {data['button']}")
                    print(f"  红外信号: {data['ir_data']['signal']}")
                    print(f"  协议: {data['ir_data']['protocol']}")
                    print(f"  已绑定: {data['is_bound']}")
                else:
                    print(f"? {button['name']} 点击未识别")
            else:
                print(f"✗ {button['name']} 点击测试失败")
        except Exception as e:
            print(f"✗ {button['name']} 测试异常: {e}")
    
    # 3. 测试协议切换
    print("\n3. 测试红外协议切换...")
    protocols = ["NEC", "RC5", "RC6", "Sony", "SAMSUNG"]
    
    for protocol in protocols:
        try:
            response = requests.post(
                f"{base_url}/switch_protocol",
                json={"protocol": protocol}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✓ 切换到 {protocol} 协议成功")
                    
                    # 测试该协议下的信号模拟
                    ir_response = requests.get(f"{base_url}/simulate_ir_signal")
                    if ir_response.status_code == 200:
                        ir_data = ir_response.json()
                        print(f"  信号模拟: {ir_data['signal']} [{ir_data['protocol']}]")
                else:
                    print(f"✗ 切换到 {protocol} 协议失败")
            else:
                print(f"✗ 协议切换请求失败")
        except Exception as e:
            print(f"✗ 协议切换异常: {e}")
    
    # 4. 测试信号绑定
    print("\n4. 测试信号绑定...")
    test_bindings = [
        {"button": "up", "signal": "0x20DF02FD", "protocol": "NEC"},
        {"button": "down", "signal": "0x20DF827D", "protocol": "NEC"},
        {"button": "enter", "signal": "0x20DF22DD", "protocol": "NEC"}
    ]
    
    for binding in test_bindings:
        try:
            response = requests.post(
                f"{base_url}/bind_signal",
                json=binding
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✓ {binding['button']} 按键绑定成功: {binding['signal']}")
                else:
                    print(f"✗ {binding['button']} 按键绑定失败")
            else:
                print(f"✗ 绑定请求失败")
        except Exception as e:
            print(f"✗ 绑定异常: {e}")
    
    # 5. 测试获取绑定信息
    print("\n5. 测试获取绑定信息...")
    try:
        response = requests.get(f"{base_url}/bindings")
        if response.status_code == 200:
            bindings = response.json()
            print(f"✓ 绑定信息获取成功，共 {len(bindings)} 个绑定:")
            for button, info in bindings.items():
                print(f"  {button}: {info['signal']} [{info['protocol']}]")
        else:
            print("✗ 绑定信息获取失败")
    except Exception as e:
        print(f"✗ 获取绑定信息异常: {e}")
    
    # 6. 测试红外接收器模块
    print("\n6. 测试红外接收器模块...")
    try:
        for protocol in ["NEC", "RC5", "Sony"]:
            ir_receiver.set_protocol(protocol)
            signal_data = ir_receiver.simulate_signal("up")
            print(f"✓ {protocol} 协议上键信号: {signal_data['signal']}")
        
        # 测试等待信号
        signal_data = ir_receiver.wait_for_signal(1.0)
        print(f"✓ 等待信号测试: {signal_data['signal']} [{signal_data['protocol']}]")
        
    except Exception as e:
        print(f"✗ 红外接收器测试异常: {e}")
    
    print("\n==========================================")
    print("功能测试完成！")
    print("请访问 http://localhost:5000 查看完整界面")
    print("==========================================")

if __name__ == "__main__":
    test_remote_app()