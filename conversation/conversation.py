from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from pymongo import MongoClient
import os
import openai

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY_FOR_SESSION")  # 用于Flask session

client = MongoClient('mongodb', 27017)
db = client['pr_review']
collection = db['review_comments_and_conversations']

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.before_request
def require_login():
    # 列出不需要登录就可以访问的端点
    allowed_routes = ['login', 'healthz']
    if 'logged_in' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

@app.route('/healthz')
def healthz():
    # 目前比较简单，后续可以添加任何需要的健康检查逻辑
    return "Healthy", 200

@app.route('/conversation')
def index():
    if 'logged_in' in session:
        return render_template('template.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.getenv("LOGIN_PASSWORD"):  # 替换为您的密码
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return "Wrong password!", 401
    return '''
        <form method="post">
            Password: <input type="password" name="password">
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/get-conversation/<uuid>', methods=['GET'])
def get_conversation(uuid):
    conversation = collection.find_one({"uuid": uuid})
    messages = conversation.get('messages', []) if conversation else []
    return jsonify(messages)

@app.route('/add-message', methods=['POST'])
def add_message():
    data = request.json
    uuid = data['uuid']
    user_message = {
        "role": "user",
        "content": data['content']
    }

    # 将用户消息保存到MongoDB
    collection.update_one({"uuid": uuid}, {"$push": {"messages": user_message}})
    # 从MongoDB中获取与该uuid相关的历史对话
    conversation = collection.find_one({"uuid": uuid})
    messages = conversation.get('messages', []) if conversation else []

    # Don't include the initial system prompt when generating subsequent conversation. Ref: issue #41
    if len(messages) > 1 and messages[0].get("role") == "system":
        # Exclude the first message (initial system prompt)
        messages_to_send = messages[1:]
    else:
        # Otherwise, send all messages
        messages_to_send = messages

    completion = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=messages_to_send
    )
    gpt_response = completion.choices[0].message

    # 将GPT-4的回复保存到MongoDB
    collection.update_one({"uuid": uuid}, {"$push": {"messages": gpt_response}})

    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0')
