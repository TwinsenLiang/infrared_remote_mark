#!/bin/bash

# 苹果A1294遥控器红外信号录制系统 - 统一服务管理脚本
# 
# 用法: ./service.sh [start|stop|restart|status|logs|help]
#
# 命令说明:
#   start   - 后台启动服务
#   stop    - 停止服务
#   restart - 重启服务
#   status  - 查看服务状态
#   logs    - 查看实时日志
#   help    - 显示帮助信息

# 定义变量
APP_NAME="infrared_remote"
PID_FILE="app.pid"
LOG_FILE="logs/app.log"

# 显示帮助信息
show_help() {
    echo "苹果A1294遥控器红外信号录制系统 - 服务管理脚本"
    echo ""
    echo "用法: $0 [start|stop|restart|status|logs|help]"
    echo ""
    echo "命令说明:"
    echo "  start   - 后台启动服务"
    echo "  stop    - 停止服务"  
    echo "  restart - 重启服务"
    echo "  status  - 查看服务状态"
    echo "  logs    - 查看实时日志"
    echo "  help    - 显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动服务"
    echo "  $0 status   # 查看状态"
    echo "  $0 logs     # 查看日志"
    echo "  $0 stop     # 停止服务"
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "错误: 未找到Python3，请先安装Python3"
        exit 1
    fi
}

# 检查虚拟环境
check_venv() {
    if [ ! -d "venv" ]; then
        echo "正在创建虚拟环境..."
        python3 -m venv venv
        
        if [ $? -ne 0 ]; then
            echo "错误: 虚拟环境创建失败"
            exit 1
        fi
    fi
}

# 安装依赖
install_deps() {
    echo "检查并安装依赖包..."
    source venv/bin/activate
    pip install -r requirements.txt > /dev/null 2>&1
    
    if [ $? -ne 0 ]; then
        echo "错误: 依赖包安装失败"
        exit 1
    fi
    
    echo "依赖包检查完成"
}

# 启动服务
start_service() {
    echo "=========================================="
    echo "苹果A1294遥控器红外信号录制系统 - 启动服务"
    echo "=========================================="
    
    # 检查服务是否已经运行
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null 2>&1; then
            echo "服务已经在运行中 (PID: $PID)"
            echo "如需重启，请使用: $0 restart"
            exit 1
        else
            echo "PID文件存在但进程不存在，清理旧的PID文件"
            rm -f $PID_FILE
        fi
    fi
    
    # 检查环境和依赖
    check_python
    check_venv
    install_deps
    
    # 创建日志目录
    mkdir -p logs
    
    echo "正在启动Web应用..."
    
    # 激活虚拟环境并启动
    source venv/bin/activate
    nohup python app.py > "$LOG_FILE" 2>&1 &
    PID=$!
    
    # 保存PID
    echo $PID > $PID_FILE
    
    # 等待启动
    sleep 2
    
    # 检查进程是否真的在运行
    if ps -p $PID > /dev/null 2>&1; then
        echo "✓ 服务启动成功!"
        echo "  PID: $PID"
        echo "  访问地址: http://localhost:5000"
        echo "  日志文件: $LOG_FILE"
        echo ""
        echo "管理命令:"
        echo "  $0 status - 查看状态"
        echo "  $0 logs   - 查看日志"
        echo "  $0 stop   - 停止服务"
    else
        echo "✗ 服务启动失败，请检查日志: $LOG_FILE"
        rm -f $PID_FILE
        exit 1
    fi
}

# 停止服务
stop_service() {
    echo "=========================================="
    echo "苹果A1294遥控器红外信号录制系统 - 停止服务"
    echo "=========================================="
    
    # 检查PID文件是否存在
    if [ ! -f "$PID_FILE" ]; then
        echo "服务未运行（PID文件不存在）"
        exit 0
    fi
    
    # 读取PID
    PID=$(cat $PID_FILE)
    
    # 检查进程是否存在
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "进程不存在 (PID: $PID)，清理PID文件"
        rm -f $PID_FILE
        exit 0
    fi
    
    echo "正在停止服务 (PID: $PID)..."
    
    # 尝试优雅停止
    kill $PID
    
    # 等待进程结束
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            echo "✓ 服务已优雅停止"
            rm -f $PID_FILE
            exit 0
        fi
        echo "等待进程结束... ($i/10)"
        sleep 1
    done
    
    # 如果优雅停止失败，强制停止
    echo "优雅停止失败，强制停止服务..."
    kill -9 $PID
    
    # 再次检查
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "✓ 服务已强制停止"
        rm -f $PID_FILE
        exit 0
    else
        echo "✗ 无法停止服务，请手动检查"
        exit 1
    fi
}

# 重启服务
restart_service() {
    echo "=========================================="
    echo "苹果A1294遥控器红外信号录制系统 - 重启服务"
    echo "=========================================="
    
    echo "正在停止服务..."
    stop_service
    
    echo ""
    echo "正在启动服务..."
    start_service
}

# 查看服务状态
show_status() {
    echo "=========================================="
    echo "苹果A1294遥控器红外信号录制系统 - 服务状态"
    echo "=========================================="
    
    # 检查PID文件是否存在
    if [ ! -f "$PID_FILE" ]; then
        echo "服务状态: 未运行"
        echo "PID文件不存在"
        echo ""
        echo "启动服务: $0 start"
        exit 0
    fi
    
    # 读取PID
    PID=$(cat $PID_FILE)
    
    # 检查进程是否存在
    if ps -p $PID > /dev/null 2>&1; then
        # 获取进程信息
        CMDLINE=$(ps -p $PID -o cmd --no-headers)
        START_TIME=$(ps -p $PID -o lstart --no-headers)
        CPU_USAGE=$(ps -p $PID -o %cpu --no-headers)
        MEM_USAGE=$(ps -p $PID -o %mem --no-headers)
        
        echo "服务状态: ✓ 正在运行"
        echo "进程ID: $PID"
        echo "启动时间: $START_TIME"
        echo "CPU使用: ${CPU_USAGE}%"
        echo "内存使用: ${MEM_USAGE}%"
        echo "命令行: $CMDLINE"
        echo ""
        echo "访问地址: http://localhost:5000"
        echo "日志文件: $LOG_FILE"
        echo ""
        echo "管理命令:"
        echo "  $0 logs     - 查看日志"
        echo "  $0 restart  - 重启服务"
        echo "  $0 stop     - 停止服务"
        
        # 检查端口是否在监听
        echo ""
        echo "端口监听状态:"
        if command -v netstat &> /dev/null; then
            if netstat -tlnp 2>/dev/null | grep ":5000 " > /dev/null; then
                echo "  端口5000: ✓ 正在监听"
            else
                echo "  端口5000: ✗ 未监听"
            fi
        elif command -v ss &> /dev/null; then
            if ss -tlnp 2>/dev/null | grep ":5000 " > /dev/null; then
                echo "  端口5000: ✓ 正在监听"
            else
                echo "  端口5000: ✗ 未监听"
            fi
        else
            echo "  (无法检查端口状态，缺少netstat或ss命令)"
        fi
        
    else
        echo "服务状态: ✗ 进程不存在"
        echo "PID文件存在但进程不在运行"
        echo "清理PID文件..."
        rm -f $PID_FILE
        echo ""
        echo "启动服务: $0 start"
    fi
}

# 查看日志
show_logs() {
    echo "=========================================="
    echo "苹果A1294遥控器红外信号录制系统 - 实时日志"
    echo "=========================================="
    echo "按 Ctrl+C 退出日志查看"
    echo ""
    
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "日志文件不存在: $LOG_FILE"
        echo "请先启动服务: $0 start"
    fi
}

# 主程序
main() {
    case "$1" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        help|--help|-h|"")
            show_help
            ;;
        *)
            echo "错误: 未知命令 '$1'"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"