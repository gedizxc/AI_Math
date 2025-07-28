from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from flask_cors import CORS
import requests
import json
import os
from dotenv import load_dotenv
import time

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)

# DeepSeek API配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "sk-7d91bc8424be449a8f9739006d709888"  # 从api_key.md文件读取

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求（非流式）"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 构建数学奥赛题解答的提示词
        system_prompt = """你是一位专业的数学奥赛题解答专家，具有深厚的数学功底和丰富的竞赛经验。

重要：必须在回答的第一句话就标明题目类型，格式为：【题目类型：具体类型】

你的任务是：
1. 立即分析题目类型，从以下类别中选择最合适的1-2个：代数、几何、数论、组合、概率、函数、不等式、解析几何
2. 仔细分析用户提供的数学题目
3. 提供详细的解题思路和步骤
4. 给出完整的解答过程
5. 解释关键概念和定理
6. 提供多种解题方法（如果适用）

请确保：
- 解答准确无误
- 步骤清晰易懂
- 使用标准的数学符号和格式
- 适当使用LaTeX格式表示数学公式，特别是对于最终答案使用\\boxed{}格式
- 提供思路分析，不仅仅是答案

回答格式要求：
第一句话必须是：【题目类型：代数,几何】（选择适合的类型，用逗号分隔）
然后换行开始正式解答。

现在请解答用户的问题："""
        
        # 准备请求DeepSeek API的数据
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {API_KEY}'
        }
        
        payload = {
            'model': 'deepseek-chat',
            'messages': [
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': user_message
                }
            ],
            'temperature': 0.3,
            'max_tokens': 3000
        }
        
        # 调用DeepSeek API
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            return jsonify({
                'response': ai_response,
                'status': 'success'
            })
        else:
            return jsonify({
                'error': f'API调用失败: {response.status_code}',
                'details': response.text
            }), 500
            
    except Exception as e:
        return jsonify({
            'error': f'服务器错误: {str(e)}'
        }), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """处理流式聊天请求"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 构建数学奥赛题解答的提示词
        system_prompt = """你是一位专业的数学奥赛题解答专家，具有深厚的数学功底和丰富的竞赛经验。

重要：必须在回答的第一句话就标明题目类型，格式为：【题目类型：具体类型】

你的任务是：
1. 立即分析题目类型，从以下类别中选择最合适的1-2个：代数、几何、数论、组合、概率、函数、不等式、解析几何
2. 仔细分析用户提供的数学题目
3. 提供详细的解题思路和步骤
4. 给出完整的解答过程
5. 解释关键概念和定理
6. 提供多种解题方法（如果适用）

请确保：
- 解答准确无误
- 步骤清晰易懂
- 使用标准的数学符号和格式
- 适当使用LaTeX格式表示数学公式，特别是对于最终答案使用\\boxed{}格式
- 提供思路分析，不仅仅是答案

回答格式要求：
第一句话必须是：【题目类型：代数,几何】（选择适合的类型，用逗号分隔）
然后换行开始正式解答。

现在请解答用户的问题："""
        
        def generate():
            try:
                # 准备请求DeepSeek API的数据
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {API_KEY}'
                }
                
                payload = {
                    'model': 'deepseek-chat',
                    'messages': [
                        {
                            'role': 'system',
                            'content': system_prompt
                        },
                        {
                            'role': 'user',
                            'content': user_message
                        }
                    ],
                    'temperature': 0.3,
                    'max_tokens': 3000,
                    'stream': True
                }
                
                # 调用DeepSeek API（流式）
                response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, stream=True)
                
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data = line[6:]  # 移除 'data: ' 前缀
                                if data == '[DONE]':
                                    yield f'data: [DONE]\n\n'
                                    break
                                try:
                                    parsed = json.loads(data)
                                    if 'choices' in parsed and len(parsed['choices']) > 0:
                                        choice = parsed['choices'][0]
                                        if 'delta' in choice and 'content' in choice['delta']:
                                            content = choice['delta']['content']
                                            yield f'data: {json.dumps({"content": content})}\n\n'
                                except json.JSONDecodeError:
                                    continue
                else:
                    error_msg = f'API调用失败: {response.status_code}'
                    yield f'data: {json.dumps({"error": error_msg})}\n\n'
                    
            except Exception as e:
                error_msg = f'服务器错误: {str(e)}'
                yield f'data: {json.dumps({"error": error_msg})}\n\n'
        
        return Response(stream_with_context(generate()), 
                       mimetype='text/plain',
                       headers={'Cache-Control': 'no-cache',
                               'Connection': 'keep-alive',
                               'Access-Control-Allow-Origin': '*',
                               'Access-Control-Allow-Headers': 'Content-Type'})
        
    except Exception as e:
        return jsonify({
            'error': f'服务器错误: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'healthy', 'message': '数学奥赛题解答助手 API 运行正常'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=50000) 
