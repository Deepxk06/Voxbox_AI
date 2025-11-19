# app_groq.py - Python Flask Backend with Groq and TTS-enabled HTML/JS Frontend

from flask import Flask, request, jsonify, render_template_string
# CORRECTED IMPORT: Should be 'from groq import Groq, types', not 'from app_groq import...'
from groq import Groq, types 
import json 

# --- 1. GROQ API SETUP (PYTHON BACKEND) ---

# !!! IMPORTANT: PASTE YOUR GROQ API KEY HERE !!!
GROQ_API_KEY = "" # Your key is now securely pasted
# !!! IMPORTANT: CHANGED MODEL NAME to a currently supported one !!!
model_name = 'llama-3.1-8b-instant' 

# Initialize the Groq Client
try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"Warning: Groq Client initialization failed. Check your API key. Error: {e}")
    client = None

# --- 2. FLASK SERVER SETUP ---
app = Flask(__name__)

# System instruction for the chatbot's personality
SYSTEM_PROMPT = {
    "role": "system", 
    "content": """
You are VoxBox, an intelligent, fast, and friendly voice assistant powered by Groq.
- Always identify yourself ONLY as "VoxBox".
- NEVER mention Groq, Llama, AI models, LLMs, or technical systems.
- Keep answers short and concise (2-4 sentences) suitable for a voice assistant.
- Provide accurate, factual, helpful answers.
"""
}

# --- 3. API CHAT ROUTE (Securely handles the API Key and History) ---
@app.route('/api/chat', methods=['POST'])
def chat():
    # Basic check to ensure the client is ready
    if not client or GROQ_API_KEY == "YOUR_GROQ_API_KEY": # Retaining this fallback check just in case
        return jsonify({"text": "Error: AI client is not initialized. Please ensure your API key is set correctly in app_groq.py."}), 500

    try:
        data = request.json
        client_contents = data.get('contents')

        if not client_contents:
            return jsonify({"error": "No content provided."}), 400
        
        # 1. Adapt history from client format (Gemini-style) to Groq/OpenAI format (list of dicts)
        messages = [SYSTEM_PROMPT]
        
        for msg in client_contents:
            role = 'assistant' if msg['role'] == 'model' else 'user'
            content = msg['parts'][0]['text']
            messages.append({"role": role, "content": content})

        # 2. Call the Groq API
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=250 
        )

        responseText = response.choices[0].message.content
        
        # Strict post-processing filter to enforce VoxBox identity
        finalResponse = responseText.replace("Groq", "VoxBox")
        finalResponse = finalResponse.replace("Llama", "VoxBox")
        finalResponse = finalResponse.replace("LLM", "assistant")
        finalResponse = finalResponse.replace("Language Model", "assistant")
        finalResponse = finalResponse.replace("as an AI", "I'm VoxBox")

        return jsonify({"text": finalResponse})

    except Exception as e:
        print(f"Groq API Error: {e}")
        # Return a generic error to the client, but log the specific Groq error
        return jsonify({"text": "An internal error occurred while processing your Groq request. Please try again."}), 500

# --- 4. HTML/JAVASCRIPT FRONTEND ROUTE ---
@app.route('/')
def index():
    # The frontend code remains unchanged as it doesn't care about the backend API used.
    # I am embedding the full HTML/JS here again for completeness, ensuring all features are present.
    return render_template_string(
        """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VoxBox AI Chat (Groq/Flask)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        .animate-pulse-slow { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        .message-bubble { max-width: 80%; padding: 12px 16px; border-radius: 18px; line-height: 1.6; }
        .thinking-dot { width: 8px; height: 8px; background-color: #60a5fa; border-radius: 50%; animation: bounce 1s infinite ease-in-out; }
        .thinking-dot:nth-child(2) { animation-delay: 0.15s; }
        .thinking-dot:nth-child(3) { animation-delay: 0.3s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1.0); }
        }
    </style>
</head>
<body class="h-screen m-0">
    <div id="app" class="flex flex-col h-full bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <div class="bg-white shadow-lg border-b border-blue-100 sticky top-0 z-10">
            <div class="max-w-4xl mx-auto px-4 py-4 flex items-center gap-3">
                <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-md">
                    <i data-lucide="sparkles" class="w-6 h-6 text-white"></i>
                </div>
                <h1 class="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">VoxBox AI Chat (Groq)</h1>
                <div id="status-indicator" class="ml-auto hidden items-center gap-2 text-blue-600">
                    <i data-lucide="volume-2" id="volume-icon" class="w-5 h-5"></i>
                    <span id="status-text" class="text-sm font-medium"></span>
                </div>
            </div>
        </div>

        <div id="messages-container" class="flex-1 overflow-y-auto px-4 py-6">
            <div id="messages-list" class="max-w-4xl mx-auto space-y-4">
                </div>
            <div id="messages-end"></div>
        </div>

        <div class="bg-white border-t border-gray-200 shadow-xl">
            <div class="max-w-4xl mx-auto px-4 py-4">
                <div class="flex gap-2 items-end">
                    <button id="mic-button" disabled class="p-3 bg-gray-300 rounded-xl disabled:opacity-50" title="Voice Input (Not enabled in this version)">
                        <i data-lucide="mic" class="w-6 h-6 text-gray-700"></i>
                    </button>
                    
                    <input
                        type="text"
                        id="user-input"
                        placeholder="Type your message..."
                        class="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    
                    <button
                        id="send-button"
                        class="p-3 bg-gradient-to-br from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed rounded-xl shadow-md transition-all"
                        title="Send message"
                    >
                        <i data-lucide="send" class="w-6 h-6 text-white"></i>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const messagesList = document.getElementById('messages-list');
            const messagesEnd = document.getElementById('messages-end');
            const userInput = document.getElementById('user-input');
            const sendButton = document.getElementById('send-button');
            const statusIndicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('status-text');
            const volumeIcon = document.getElementById('volume-icon');
            const API_ENDPOINT = '/api/chat';

            let messages = [
                { role: 'model', content: "Hi! I'm VoxBox, your intelligent assistant. How can I help you today?" }
            ];

            // --- TEXT-TO-SPEECH (TTS) FUNCTIONS ---
            function speakText(text) {
                if (!('speechSynthesis' in window)) {
                    console.warn('Speech Synthesis not supported.');
                    return;
                }
                
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 1.0;
                utterance.pitch = 1.0;
                
                utterance.onstart = () => {
                    statusText.textContent = 'Speaking...';
                    statusIndicator.classList.add('flex');
                    statusIndicator.classList.remove('hidden');
                    volumeIcon.classList.add('animate-pulse-slow');
                };
                utterance.onend = () => {
                    statusText.textContent = '';
                    volumeIcon.classList.remove('animate-pulse-slow');
                    statusIndicator.classList.remove('flex');
                    statusIndicator.classList.add('hidden');
                };
                
                window.speechSynthesis.speak(utterance);
            }
            
            // Renders a single message bubble
            function renderMessage(msg) {
                const isUser = msg.role === 'user';
                const messageDiv = document.createElement('div');
                messageDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'}`;
                
                const bubble = document.createElement('div');
                bubble.className = 'message-bubble shadow-md whitespace-pre-wrap ' + 
                                   (isUser 
                                        ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white' 
                                        : 'bg-white border border-gray-200 text-gray-800');
                
                bubble.textContent = msg.content;
                messageDiv.appendChild(bubble);
                messagesList.appendChild(messageDiv);
            }

            // Displays the thinking animation
            function showThinking() {
                statusText.textContent = 'Thinking...';
                volumeIcon.classList.remove('animate-pulse-slow'); 
                
                statusIndicator.classList.remove('hidden');
                statusIndicator.classList.add('flex');
                
                const thinkingDiv = document.createElement('div');
                thinkingDiv.id = 'thinking-animation';
                thinkingDiv.className = 'flex justify-start';
                
                const bubble = document.createElement('div');
                bubble.className = 'bg-white shadow-sm border border-gray-200 message-bubble';
                
                const dots = document.createElement('div');
                dots.className = 'flex gap-2';
                dots.innerHTML = '<div class="thinking-dot"></div><div class="thinking-dot"></div><div class="thinking-dot"></div>';

                bubble.appendChild(dots);
                thinkingDiv.appendChild(bubble);
                messagesList.appendChild(thinkingDiv);
                scrollToBottom();
            }

            // Hides the thinking animation
            function hideThinking() {
                const thinkingDiv = document.getElementById('thinking-animation');
                if (thinkingDiv) {
                    thinkingDiv.remove();
                }
                if (statusText.textContent !== 'Speaking...') {
                    statusIndicator.classList.remove('flex');
                    statusIndicator.classList.add('hidden');
                }
            }

            function scrollToBottom() {
                messagesEnd.scrollIntoView({ behavior: 'smooth' });
            }

            async function handleSendMessage() {
                const messageText = userInput.value.trim();
                if (!messageText) return;
                
                if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                }

                // 1. User Message: Add to state and render
                const userMessage = { role: 'user', content: messageText };
                messages.push(userMessage);
                renderMessage(userMessage);
                userInput.value = '';
                
                showThinking();
                sendButton.disabled = true;

                try {
                    // 2. Prepare history for the backend (Groq/Gemini-like format is fine for transport)
                    const contentsForAPI = messages.map(msg => ({
                        role: msg.role,
                        parts: [{ text: msg.content }]
                    }));

                    // 3. Send request to Flask backend
                    const response = await fetch(API_ENDPOINT, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ contents: contentsForAPI }),
                    });

                    if (!response.ok) {
                        throw new Error('Server or API error.');
                    }

                    const data = await response.json();
                    
                    // 4. Assistant Response: Add to state and render
                    const assistantMessage = { role: 'model', content: data.text.trim() };
                    messages.push(assistantMessage);
                    renderMessage(assistantMessage);
                    
                    // 5. TTS Feature: Speak the response aloud
                    speakText(assistantMessage.content);

                } catch (error) {
                    console.error('Chat Error:', error);
                    const errorMessage = {
                        role: 'model',
                        content: "Sorry, I ran into an issue. Please check the server, your Groq API key, and try again."
                    };
                    messages.push(errorMessage);
                    renderMessage(errorMessage);
                    speakText(errorMessage.content);
                } finally {
                    hideThinking();
                    sendButton.disabled = false;
                    scrollToBottom();
                }
            }

            // Event Listeners
            sendButton.addEventListener('click', handleSendMessage);
            userInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSendMessage();
                }
            });
            
            // Initial rendering and icon creation
            function renderInitial() {
                messages.forEach(renderMessage);
                scrollToBottom();
                lucide.createIcons();
                // Speak the initial greeting
                speakText(messages[0].content);
            }
            
            renderInitial();
        });
    </script>
</body>
</html>
"""
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)