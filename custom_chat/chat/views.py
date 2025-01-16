from django.shortcuts import render # Importing the 'render' function from Django to render HTML templates
import json # Importing the 'json' module to work with JSON data
import random # Importing the 'random' module to disconnect randomly
from django.http import JsonResponse # Importing the 'JsonResponse' class from Django to return JSON responses to HTTP requests
from django.views.decorators.csrf import csrf_exempt # Decorator to exempt the view from CSRF verification (Cross-Site Request Forgery)
import os # Importing the 'os' module to interact with the operating system


# Define constants for file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE_PATH = os.path.join(BASE_DIR, "keywords.json")
LOG_FILE_PATH = os.path.join(BASE_DIR, "chat_logs.json")

# Load configuration
def load_config():
    if not os.path.exists(KEY_FILE_PATH):
        raise FileNotFoundError(f"Configuration file '{KEY_FILE_PATH}' not found.")
    with open(KEY_FILE_PATH, "r") as file:
        return json.load(file)

CONFIG = load_config()

# Load or initialize chat logs
def load_chat_logs():
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "w") as file:
            json.dump([], file)  # Initialize with an empty list if file doesn't exist
    try:
        with open(LOG_FILE_PATH, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        # If file is corrupt or empty, reset with an empty list
        return []

# Save chat logs to file
def save_chat_logs(data):
    try:
        with open(LOG_FILE_PATH, "w") as file:
            json.dump(data, file, indent=4)
            print("Chat logs saved successfully.")
    except Exception as e:
        print(f"Error saving chat logs: {e}")
# Chat view
@csrf_exempt
def chat_view(request):
    try:
        if request.method == 'GET':
            return render(request, 'chat.html')

        if request.method == 'POST':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON payload."}, status=400)

            user_name = data.get('user_name', 'User')
            message = data.get('message', None) 

            # Load chat logs
            chat_logs = load_chat_logs()
            session = next((s for s in chat_logs if s["user_name"].lower() == user_name.lower()), None)

            # Create a new session if it doesn't exist
            if not session:
                agent_name = random.choice(CONFIG["agent_names"])
                session = {
                    "session_id": len(chat_logs) + 1,
                    "user_name": user_name,
                    "agent_name": agent_name,
                    "messages": [
                        {agent_name: f"Hi, I am {agent_name}. How can I help you?"}
                    ],
                    "ended": False
                }
                chat_logs.append(session)
                save_chat_logs(chat_logs)

                # Return only the greeting for a new session
                return JsonResponse({
                    "response": session["messages"][-1][agent_name], 
                    "messages": session["messages"],
                    "user_exists": False,
                })
            
            # Handle a previously ended session
            if session.get("ended",False):
                # Session ended: Allow user to continue and reset 'ended' status  # Reset the session as active again
                session["ended"] = False
                agent_greeting = f"Hi again, {user_name}! What can I help you with this time?"
                session["messages"].append({session["agent_name"]: agent_greeting})
                      
                # Save the updated session data
                save_chat_logs(chat_logs)

                return JsonResponse({
                    "response": agent_greeting,
                    "end_chat": False, 
                    "messages": session["messages"],
                    "user_exists": True
                })
            
            if not message.strip():
                return JsonResponse({"error": "Message cannot be empty."}, status=400)

            
            if random.random() < 0.04:
                session["ended"] = True
                save_chat_logs(chat_logs)
                return JsonResponse({
                    "response": "You have been disconnected due to inactivity. Please refresh the page to continue your chat.",
                    "end_chat": True,
                    "messages": session["messages"]
                })
            
            
            # Check if the user is trying to end the chat (goodbye or exit)
            end_keywords = ["bye", "goodbye", "exit", "quit"]
            message_words = set(message.lower().split())
            if any(end_keyword in message.lower() in message_words for end_keyword in end_keywords):
                session["messages"].append({user_name: message})
                goodbye_message = random.choice(CONFIG["keywords"]["quit"]).replace("{user_name}", user_name)
                session["messages"].append({session["agent_name"]: goodbye_message})
                session["ended"] = True
                save_chat_logs(chat_logs)
                return JsonResponse({
                    "response": goodbye_message,
                    "end_chat": True,
                    "messages": session["messages"]
                })
            
            # Process multi-keyword responses
            matched_responses = []
            for keyword, replies in CONFIG["keywords"].items():
                if keyword.lower() in message.lower():
                    matched_responses.append(random.choice(replies).replace("{user_name}", user_name))

            # If no matched responses, check for greeting responses
            if not matched_responses:
                greeting_keywords = ["hi", "hello", "how are you"]
                if any(greeting in message.lower() for greeting in greeting_keywords):
                    response = random.choice(CONFIG["keywords"]["greetings"])
                else:
                    # If no keywords match and no greetings, choose a random response
                    response = random.choice(CONFIG["random_responses"])
            
            # If matched responses exist, use them
            if matched_responses:
                response = " ".join(matched_responses)
            
            # Replace placeholders in the response
            response = response.replace("{user_name}", user_name).replace("{agent_name}", session["agent_name"])
            
            session["messages"].append({user_name: message}) 
            session["messages"].append({session["agent_name"]: response})
            save_chat_logs(chat_logs)

        return JsonResponse({"response": response, "messages": session["messages"]})
    
    except Exception as e:
    
        return JsonResponse({"error": "Invalid request method."}, status=400)

# View to get chat history of existing user    
@csrf_exempt
def get_chat_history(request, user_name):
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
    
    try:
        chat_logs = load_chat_logs()
        user_sessions = [session for session in chat_logs if session['user_name'].lower() == user_name.lower()]
        
        if not user_sessions:
            return JsonResponse([], safe=False)  # No history found

        # Combine all messages from all sessions
        all_messages = []
        for session in user_sessions:
            for msg in session['messages']:
                # Identify agent messages 
                agent_name = session['agent_name']
                if agent_name in msg:
                    all_messages.append({
                        "agent_name": agent_name,
                        "message": msg[agent_name]
                    })
                elif user_name in msg:
                    # Optionally include user messages as well
                    all_messages.append({
                        "user_name": user_name,
                        "message": msg[user_name]
                    })
        
        return JsonResponse(all_messages, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# View to delete chat history for a user
@csrf_exempt
def delete_chat_history(request, user_name):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
    
    try:
        chat_logs = load_chat_logs()

        user_name = user_name.strip().lower()
        # Filter out all sessions related to the user
        new_chat_logs = [session for session in chat_logs if session['user_name'].strip().lower() != user_name]
        
        if len(new_chat_logs) == len(chat_logs):
            return JsonResponse({'error': 'No chat history found for the user.'}, status=404)
        
        # Save the updated chat logs
        save_chat_logs(new_chat_logs)
        
        return JsonResponse({'message': 'Chat history deleted successfully.'}, status=200)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)