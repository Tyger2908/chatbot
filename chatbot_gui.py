import os
import json
import requests
import tkinter as tk
import webbrowser
import re
import wikipediaapi
from nltk.chat.util import Chat, reflections
from textblob import TextBlob
import sympy as sp

# Load patterns from the JSON file
def load_patterns(filename='responses.json'):
    with open(filename, 'r') as file:
        data = json.load(file)

    patterns = []
    for intent in data['intents']:
        for pattern in intent['patterns']:
            patterns.append((pattern, intent['responses']))
    
    return patterns

# Normalize user input
def normalize_input(user_input):
    corrected_input = str(TextBlob(user_input).correct())
    if corrected_input.lower() == user_input.lower():
        return user_input.strip()
    return corrected_input.strip()

# Get weather information
def get_weather(city):
    api_key = "4c58d1bbe11efefea68e3eed7fb2907f"  # Replace with your actual API key
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if data["cod"] == 200:
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            return (f"The weather in {city} is currently {weather} with a temperature of {temp:.2f}°C. "
                    f"It feels like {feels_like:.2f}°C.")
        elif data["cod"] == "404":
            return f"Sorry, I couldn't find the weather for {city}. Please check the spelling."
        elif data["cod"] == "401":
            return "Unauthorized: Please check your API key."
        else:
            return f"Sorry, I couldn't retrieve the weather data at this moment. (Error code: {data['cod']})"
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}. Please try again later."

# Initialize chatbot patterns
patterns = load_patterns()
chatbot = Chat(patterns, reflections)

class ChatbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Chatbot")
        self.root.geometry("900x800")  # Increased window size
        self.root.configure(bg="#262626")

        # Create a Canvas for chat bubbles
        self.chat_canvas = tk.Canvas(root, bg="#4d4d4d")
        self.chat_canvas.place(x=20, y=20, height=650, width=860)

        self.scrollbar = tk.Scrollbar(root, command=self.chat_canvas.yview, width=8, troughcolor="#4d4d4d", bg="#4d4d4d", activebackground="#0A6742", highlightcolor="#4d4d4d")
        self.scrollbar.place(x=880, y=20, height=650, width=10)
        self.chat_canvas.config(yscrollcommand=self.scrollbar.set)
        
        # Bind mouse wheel for scrolling
        self.chat_canvas.bind("<MouseWheel>", self.on_mouse_wheel)

        # Message entry box
        self.message_box = tk.Entry(root, bg="#333333", font=("Arial", 12), fg="white", relief="solid", borderwidth=1)
        self.message_box.place(x=20, y=680, height=35, width=600)
        self.message_box.bind("<Return>", self.send_message)  # Press Enter to send

        # Send button
        self.send_button = tk.Button(root, text="SEND", command=self.send_message, bg="#2E6F40", fg="black", cursor="hand2", font=("Arial", 14, "bold"), activebackground="#2E6F40", activeforeground="black", relief="solid", borderwidth=2, width=10, height=2)
        self.send_button.place(x=640, y=680, height=40)
        self.send_button.bind("<Enter>", lambda e: self.send_button.configure(bg="#0A6742"))  
        self.send_button.bind("<Leave>", lambda e: self.send_button.configure(bg="#2E6F40"))

        self.messages = []  # Store messages for scrolling
        self.last_y_position = 10  # Start position for the first message

        # Initialize Wikipedia API
        self.wiki_wiki = wikipediaapi.Wikipedia(
            language='en',
            user_agent="TyralChatbot/1.0 (https://github.com/Tyger2908/chatbot)"
        )

    def send_message(self, event=None):
        user_message = self.message_box.get()
        if user_message.strip():
            self.display_message(f"You: {user_message}", is_user=True)
            normalized_message = normalize_input(user_message)
            response = self.get_bot_response(normalized_message)
            self.display_message(f"Bot: {response}", is_user=False)
        self.message_box.delete(0, tk.END)

    def display_message(self, message, is_user):
        x = 20 if not is_user else 620  # Align user messages to the right
        y = self.last_y_position  # Use the stored last position to avoid overlap
        bubble_color = "#2E6F40" if is_user else "#1E1E1E"
        text_color = "white"

        # Calculate bubble dimensions based on text size
        wrapped_text = self.chat_canvas.create_text(x + 10, y + 5, text=message, fill=text_color, anchor="nw", font=("Arial", 12), width=600)
        text_bbox = self.chat_canvas.bbox(wrapped_text)
        bubble_width = min(text_bbox[2] - text_bbox[0] + 20, 740)  # Limit bubble width to fit canvas
        bubble_height = text_bbox[3] - text_bbox[1] + 20  # Add padding

        # Create a chat bubble
        bubble = self.chat_canvas.create_rectangle(x, y, x + bubble_width, y + bubble_height, fill=bubble_color, outline="")
        self.chat_canvas.create_text(x + 10, y + 10, text=message, fill=text_color, anchor="nw", font=("Arial", 12), width=600)

        # Update last_y_position for the next message
        self.last_y_position = y + bubble_height + 10  # Add some space for the next message

        self.messages.append(bubble)

        # Adjust the canvas height
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))

    def on_mouse_wheel(self, event):
        # Scroll the canvas based on the mouse wheel movement
        self.chat_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def get_bot_response(self, message):
        if "weather in" in message:
            city = message.replace("weather in", "").strip()
            return get_weather(city)

        if "google" in message.lower() or "search" in message.lower() or "internet" in message.lower():
            query = message.lower().replace("google", "").replace("search", "").replace("internet", "").strip()
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return "I've opened Google with your search query."

        if "wiki" in message.lower() or "wikipedia" in message.lower():
            query = message.replace("wiki", "").replace("wikipedia", "").strip()
            return self.fetch_from_wikipedia(query)

        if re.match(r'^[\d\s\+\-*/=.xX]+$', message):  # Check if it's a math expression
            return self.evaluate_math_expression(message)

        response = chatbot.respond(message)
        if response is None:
            response = "I'm sorry, I didn't understand that."
        return response

    def evaluate_math_expression(self, expression):
        try:
            x = sp.symbols('x')
            if '=' in expression:
                left, right = expression.split('=')
                eq = sp.Eq(sp.sympify(left.strip()), sp.sympify(right.strip()))
                solution = sp.solve(eq, x)
                return f"The solution is x = {solution[0]}" if solution else "No solution found."
            else:
                result = sp.sympify(expression)
                return f"The result is {result}"
        except Exception:
            return "Error evaluating the expression."

    def fetch_from_wikipedia(self, query):
        page = self.wiki_wiki.page(query)
        if page.exists():
            return page.summary
        else:
            return "I'm sorry, I couldn't find any information on that topic."

if __name__ == '__main__':
    root = tk.Tk()
    app = ChatbotGUI(root)
    root.mainloop()