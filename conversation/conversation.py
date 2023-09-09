from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)
client = MongoClient('localhost', 27017)
db = client['pr_review']
collection = db['review_comments_and_conversations']

@app.route('/get-conversation/<uuid>', methods=['GET'])
def get_conversation(uuid):
    conversation = collection.find_one({"uuid": uuid})
    messages = conversation.get('messages', []) if conversation else []
    return jsonify(messages)

@app.route('/add-message', methods=['POST'])
def add_message():
    data = request.json
    uuid = data['uuid']
    message = {
        "role": "user",
        "content": data['content']
    }
    result = collection.update_one({"uuid": uuid}, {"$push": {"messages": message}}, upsert=True)
    print(result)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run()
