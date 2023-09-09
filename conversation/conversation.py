from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
import openai

app = Flask(__name__)
CORS(app)
client = MongoClient('localhost', 27017)
db = client['pr_review']
collection = db['review_comments_and_conversations']

openai.api_key = os.getenv("OPENAI_API_KEY")

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

    # 调用GPT-4 API获取回复
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        max_tokens=300,
        temperature=0.5,
        messages=messages
    )
    gpt_response = completion.choices[0].message

    # 将GPT-4的回复保存到MongoDB
    collection.update_one({"uuid": uuid}, {"$push": {"messages": gpt_response}})

    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run()
