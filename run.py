#!/usr/bin/env python3
"""
DeepSeek AI 聊天应用启动脚本
"""

from app import app

if __name__ == '__main__':
    print("🚀 启动 DeepSeek AI 聊天应用...")
    print("📱 访问地址: http://localhost:5000")
    print("🔧 API 健康检查: http://localhost:5000/api/health")
    print("⏹️  按 Ctrl+C 停止应用")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000) 