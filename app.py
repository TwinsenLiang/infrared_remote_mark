#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import xml.etree.ElementTree as ET
from flask import Flask, render_template, jsonify, request
from infrared_receiver import ir_receiver

app = Flask(__name__)

class RemoteControlAnalyzer:
    def __init__(self, svg_path):
        self.svg_path = svg_path
        self.button_positions = {}
        self.button_mapping = {}
        self.last_ir_signal = None
        self.signal_bindings = self.load_bindings()
        
        # 分析SVG并确定按键位置
        self.analyze_svg()
        
    def analyze_svg(self):
        """分析SVG文件，确定按键位置"""
        try:
            tree = ET.parse(self.svg_path)
            root = tree.getroot()
            
            # 根据SVG中的元素位置确定按键区域
            self.button_positions = {
                'up': {'center': (132, 120), 'radius': 15, 'svg_id': None},
                'down': {'center': (131, 316), 'radius': 15, 'svg_id': None},
                'left': {'center': (34, 217), 'radius': 15, 'svg_id': None},
                'right': {'center': (229, 218), 'radius': 15, 'svg_id': None},
                'enter': {'center': (131, 218), 'radius': 52, 'svg_id': None},
                'menu': {'center': (68, 402), 'radius': 47, 'svg_id': None},
                'play_pause': {'center': (194, 402), 'radius': 47, 'svg_id': None}
            }
            
            # 根据实际SVG尺寸调整坐标比例
            self.width = 262
            self.height = 1001
            
        except Exception as e:
            print(f"SVG分析错误: {e}")
            
    def is_point_in_button(self, x, y, button_name):
        """检查点击位置是否在按键区域内"""
        if button_name not in self.button_positions:
            return False
            
        button = self.button_positions[button_name]
        cx, cy = button['center']
        radius = button['radius']
        
        distance = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        return distance <= radius
        
    def get_clicked_button(self, x, y):
        """根据点击位置获取对应的按键"""
        for button_name in self.button_positions:
            if self.is_point_in_button(x, y, button_name):
                return button_name
        return None
        
    def load_bindings(self):
        """加载已绑定的红外信号"""
        try:
            with open('signal_bindings.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
            
    def save_bindings(self):
        """保存红外信号绑定"""
        with open('signal_bindings.json', 'w', encoding='utf-8') as f:
            json.dump(self.signal_bindings, f, ensure_ascii=False, indent=2)
            
    def bind_signal(self, button_name, signal_data):
        """绑定红外信号到按键"""
        self.signal_bindings[button_name] = {
            'signal': signal_data,
            'timestamp': time.time()
        }
        self.save_bindings()

    def unbind_signal(self, button_name):
        """解除按键的信号绑定"""
        if button_name in self.signal_bindings:
            del self.signal_bindings[button_name]
            self.save_bindings()
            return True
        return False

    def simulate_ir_reception(self):
        """模拟红外信号接收"""
        return ir_receiver.simulate_signal()
        
    def get_button_state(self, button_name):
        """获取按键状态（是否已绑定信号）"""
        return button_name in self.signal_bindings

# 创建遥控器分析器实例
remote_analyzer = RemoteControlAnalyzer('A1294.svg')

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')



@app.route('/api/svg_data')
def get_svg_data():
    """获取SVG数据"""
    with open('A1294.svg', 'r', encoding='utf-8') as f:
        svg_content = f.read()
    return jsonify({'svg': svg_content})

@app.route('/api/button_click', methods=['POST'])
def handle_button_click():
    """处理按键点击"""
    data = request.json
    x = data.get('x')
    y = data.get('y')
    
    button = remote_analyzer.get_clicked_button(x, y)
    if button:
        # 模拟接收红外信号
        ir_data = remote_analyzer.simulate_ir_reception()
        
        return jsonify({
            'button': button,
            'ir_data': ir_data,
            'is_bound': remote_analyzer.get_button_state(button)
        })
    
    # 点击无效区域，返回空的成功响应
    return jsonify({'success': True})

@app.route('/api/bind_signal', methods=['POST'])
def bind_signal():
    """绑定红外信号到按键"""
    data = request.json
    button_name = data.get('button')
    signal_data = data.get('signal')

    # 输入验证
    VALID_BUTTONS = ['up', 'down', 'left', 'right', 'enter', 'menu', 'play_pause']
    if not button_name or button_name not in VALID_BUTTONS:
        return jsonify({'error': '无效的按钮名称'}), 400

    # 验证信号格式 (0xXXXXXXXX)
    import re
    if not signal_data or not re.match(r'^0x[0-9A-F]{8}$', signal_data, re.IGNORECASE):
        return jsonify({'error': '无效的信号格式'}), 400

    remote_analyzer.bind_signal(button_name, signal_data)
    return jsonify({'success': True})

@app.route('/api/unbind_signal', methods=['POST'])
def unbind_signal():
    """解除按键的信号绑定"""
    data = request.json
    button_name = data.get('button')

    # 输入验证
    VALID_BUTTONS = ['up', 'down', 'left', 'right', 'enter', 'menu', 'play_pause']
    if not button_name or button_name not in VALID_BUTTONS:
        return jsonify({'error': '无效的按钮名称'}), 400

    if remote_analyzer.unbind_signal(button_name):
        return jsonify({'success': True})
    else:
        return jsonify({'error': '按键未绑定'}), 400

@app.route('/api/bindings')
def get_bindings():
    """获取所有绑定信息"""
    return jsonify(remote_analyzer.signal_bindings)

@app.route('/api/simulate_ir_signal')
def simulate_ir_signal():
    """模拟接收红外信号"""
    ir_data = remote_analyzer.simulate_ir_reception()
    return jsonify(ir_data)

@app.route('/api/wait_for_ir_signal', methods=['POST'])
def wait_for_ir_signal():
    """等待接收红外信号"""
    try:
        data = request.json
        timeout = data.get('timeout', 5.0)
        
        # 这里应该在新线程中执行，避免阻塞
        def wait_signal():
            signal_data = ir_receiver.wait_for_signal(timeout)
            return signal_data
        
        # 简化版本，直接返回
        signal_data = ir_receiver.wait_for_signal(timeout)
        return jsonify(signal_data)
        
    except Exception as e:
        return jsonify({'error': f'接收信号失败: {str(e)}'}), 500

if __name__ == '__main__':
    import os
    # 从环境变量读取配置，生产环境不开启 DEBUG
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('FLASK_PORT', '5000'))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)