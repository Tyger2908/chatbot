import os
import sys
import json
from flask import Flask, request, jsonify
from nltk.chat.util import Chat, reflections

app = Flask(__name__)

# Load patterns and responses from JSON file
def load_patterns(filename='responses.json'):
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        filename = os.path.join(bundle_dir, filename)
    with open(filename, 'r') as file:
        data = json.load(file)

    patterns = []
    for intent in data['intents']:
        for pattern in intent['patterns']:
            patterns.append((pattern, intent['responses']))
    return patterns

# Save new response to the JSON file
def save_new_response(tag, pattern, response):
    with open('responses.json', 'r+') as file:
        data = json.load(file)
        for intent in data['intents']:
            if intent['tag'] == tag:
                intent['patterns'].append(pattern)
                intent['responses'].append(response)
                break
        else:
            # If tag does not exist, create a new intent
            data['intents'].append({
                "tag": tag,
                "patterns": [pattern],
                "responses": [response]
            })
        file.seek(0)
        json.dump(data, file, indent=4)
        file.truncate()

# Initialize Chatbot
patterns = load_patterns()
chatbot = Chat(patterns, reflections)

# Route to handle chat messages
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    response = chatbot.respond(user_input)

    if response is None:
        response = "I'm sorry, I didn't understand that. Can you tell me how to respond to that?"

    return jsonify({"response": response})

# Route to handle saving new responses
@app.route('/add_response', methods=['POST'])
def add_response():
    user_input = request.json.get("message")
    new_response = request.json.get("new_response")
    
    if user_input and new_response:
        try:
            save_new_response("noanswer", user_input, new_response)
            return jsonify({"response": "Thanks! I've learned something new."})
        except Exception as e:
            return jsonify({"response": "Failed to save the response.", "error": str(e)})
    
    return jsonify({"response": "Invalid input."})

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)