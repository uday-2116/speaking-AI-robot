import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
import time
import json

# Set page configuration
st.set_page_config(
    page_title="Hey Bob - Voice Assistant",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="🎤"
)

# API Keys
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

# Check if API keys are available
if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    st.error("🔑 API keys are missing. Please check your configuration.")
    st.stop()

SYSTEM_PROMPT = """
You are Bob, a friendly and helpful voice assistant activated by the wake word "Hey Bob".

Your personality:
- Conversational and natural, like talking to a friend
- Concise but informative (2-4 sentences max for voice)
- Helpful and knowledgeable about any topic
- Always respond as if you're speaking out loud

You can help with:
- General knowledge and trivia
- Current events and news (use web search)
- Weather information  
- Technology questions
- Calculations and conversions
- Medical and health information
- Travel and local information
- And much more

Always provide responses that sound natural when spoken aloud. Avoid overly technical language unless specifically asked.
"""

@st.cache_resource
def get_agent():
    """Initialize and cache the AI agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=SYSTEM_PROMPT,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing agent: {e}")
        return None

def get_ai_response(query):
    """Get response from AI agent."""
    agent = get_agent()
    if agent is None:
        return "Sorry, I'm having trouble connecting to my knowledge base right now."
    
    try:
        response = agent.run(query)
        return response.content.strip()
    except Exception as e:
        return f"Sorry, I encountered an error while processing your question: {str(e)}"

def main():
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'assistant_active' not in st.session_state:
        st.session_state.assistant_active = False
    if 'last_query' not in st.session_state:
        st.session_state.last_query = ""

    # Custom CSS for a modern voice assistant look
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
    }
    .voice-status {
        font-size: 1.5rem;
        margin: 1rem 0;
    }
    .conversation-bubble {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        border-left: 4px solid #007bff;
    }
    .bob-response {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .wake-word {
        color: #dc3545;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Hey Bob</h1>
        <p>Your Voice-Activated AI Assistant</p>
        <p style="font-size: 0.9rem; opacity: 0.8;">Say <span class="wake-word">"Hey Bob"</span> followed by your question</p>
    </div>
    """, unsafe_allow_html=True)

    # Voice Assistant Interface
    import streamlit.components.v1 as components
    
    # Main voice interface with wake word detection
    voice_assistant_html = f"""
    <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #74b9ff, #0984e3); border-radius: 20px; margin: 20px 0; color: white;">
        
        <!-- Assistant Status -->
        <div id="assistantStatus" style="font-size: 24px; margin-bottom: 20px; font-weight: bold;">
            🎤 Assistant Ready
        </div>
        
        <!-- Main Control Button -->
        <button id="mainBtn" style="
            font-size: 80px; 
            background: rgba(255,255,255,0.2); 
            border: 3px solid white; 
            border-radius: 50%; 
            cursor: pointer; 
            padding: 25px;
            transition: all 0.3s;
            color: white;
            margin-bottom: 20px;
        ">🎤</button>
        
        <!-- Status Messages -->
        <div id="listeningStatus" style="font-size: 18px; margin: 15px 0; min-height: 30px;">
            Click to start continuous listening
        </div>
        
        <!-- Transcript Display -->
        <div id="transcriptDisplay" style="
            background: rgba(255,255,255,0.9); 
            color: #333; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 15px 0; 
            min-height: 50px;
            display: none;
            font-family: monospace;
        ">
            Transcript will appear here...
        </div>
        
        <!-- Controls -->
        <div style="margin-top: 20px;">
            <button id="stopBtn" style="
                padding: 10px 20px; 
                background: #dc3545; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer;
                margin: 5px;
                display: none;
            ">⏹️ Stop Listening</button>
        </div>
    </div>

    <script>
    let recognition;
    let isListening = false;
    let continuousMode = false;

    const mainBtn = document.getElementById('mainBtn');
    const status = document.getElementById('listeningStatus');
    const assistantStatus = document.getElementById('assistantStatus');
    const transcript = document.getElementById('transcriptDisplay');
    const stopBtn = document.getElementById('stopBtn');

    // Check for wake word
    function checkWakeWord(text) {{
        const lowerText = text.toLowerCase();
        const wakeWords = ['hey bob', 'hi bob', 'hello bob', 'bob'];
        
        for (let wake of wakeWords) {{
            if (lowerText.includes(wake)) {{
                // Extract the command after wake word
                const wakeIndex = lowerText.indexOf(wake);
                const command = text.substring(wakeIndex + wake.length).trim();
                return command || text; // Return command or full text if no command after wake word
            }}
        }}
        return null;
    }}

    // Process voice command
    function processCommand(command) {{
        transcript.innerHTML = `🎙️ <strong>You:</strong> "${{command}}"`;
        transcript.style.display = 'block';
        status.innerHTML = '🤖 Bob is thinking...';
        assistantStatus.innerHTML = '🧠 Processing...';
        
        // Send to Streamlit
        const url = new URL(window.location);
        url.searchParams.set('hey_bob_query', encodeURIComponent(command));
        url.searchParams.set('timestamp', Date.now());
        window.location.href = url.toString();
    }}

    // Start recognition
    function startRecognition() {{
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {{
            status.innerHTML = '❌ Speech recognition not supported. Use Chrome!';
            return;
        }}

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = true;  // Keep listening
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = function() {{
            isListening = true;
            continuousMode = true;
            mainBtn.style.background = 'rgba(255,0,0,0.3)';
            mainBtn.style.transform = 'scale(1.1)';
            assistantStatus.innerHTML = '👂 Listening for "Hey Bob"...';
            status.innerHTML = 'Say <strong>"Hey Bob"</strong> followed by your question';
            stopBtn.style.display = 'inline-block';
            transcript.style.display = 'block';
            transcript.innerHTML = '🎧 Listening... Say "Hey Bob" to activate';
        }};

        recognition.onresult = function(event) {{
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {{
                const transcriptPart = event.results[i][0].transcript;
                if (event.results[i].isFinal) {{
                    finalTranscript += transcriptPart;
                }} else {{
                    interimTranscript += transcriptPart;
                }}
            }}
            
            // Show live transcript
            if (interimTranscript) {{
                transcript.innerHTML = `🎧 Listening: "${{interimTranscript}}"`;
            }}
            
            // Check for wake word in final transcript
            if (finalTranscript) {{
                const command = checkWakeWord(finalTranscript);
                if (command) {{
                    // Wake word detected!
                    assistantStatus.innerHTML = '🎯 Wake word detected!';
                    recognition.stop();
                    processCommand(command);
                }} else {{
                    // Continue listening
                    transcript.innerHTML = `🎧 Heard: "${{finalTranscript}}" (no wake word)`;
                    setTimeout(() => {{
                        transcript.innerHTML = '🎧 Listening... Say "Hey Bob" to activate';
                    }}, 2000);
                }}
            }}
        }};

        recognition.onerror = function(event) {{
            status.innerHTML = `❌ Error: ${{event.error}}`;
            assistantStatus.innerHTML = '❌ Error occurred';
            
            if (event.error === 'not-allowed') {{
                status.innerHTML = '🔒 Please allow microphone access and refresh';
            }} else if (event.error === 'no-speech') {{
                // Restart recognition for continuous listening
                if (continuousMode) {{
                    setTimeout(() => {{
                        if (continuousMode) recognition.start();
                    }}, 1000);
                }}
            }}
        }};

        recognition.onend = function() {{
            mainBtn.style.background = 'rgba(255,255,255,0.2)';
            mainBtn.style.transform = 'scale(1)';
            
            if (continuousMode) {{
                // Restart for continuous listening
                setTimeout(() => {{
                    if (continuousMode && recognition) {{
                        try {{
                            recognition.start();
                        }} catch (e) {{
                            console.log('Recognition restart failed:', e);
                        }}
                    }}
                }}, 100);
            }} else {{
                isListening = false;
                assistantStatus.innerHTML = '🎤 Assistant Ready';
                status.innerHTML = 'Click to start continuous listening';
                stopBtn.style.display = 'none';
            }}
        }};

        recognition.start();
    }}

    // Stop listening
    function stopListening() {{
        continuousMode = false;
        isListening = false;
        if (recognition) {{
            recognition.stop();
        }}
        mainBtn.style.background = 'rgba(255,255,255,0.2)';
        mainBtn.style.transform = 'scale(1)';
        assistantStatus.innerHTML = '🎤 Assistant Ready';
        status.innerHTML = 'Click to start continuous listening';
        stopBtn.style.display = 'none';
        transcript.style.display = 'none';
    }}

    // Event listeners
    mainBtn.addEventListener('click', function() {{
        if (!isListening) {{
            startRecognition();
        }}
    }});

    stopBtn.addEventListener('click', stopListening);

    // Auto-start on page load (optional)
    // Uncomment the next line to auto-start listening
    // setTimeout(startRecognition, 2000);
    </script>
    """

    components.html(voice_assistant_html, height=400)

    # Process "Hey Bob" commands
    hey_bob_query = st.query_params.get("hey_bob_query")
    if hey_bob_query:
        # Clear URL params immediately
        st.query_params.clear()
        
        # Display the command
        st.markdown(f'<div class="conversation-bubble">🎙️ <strong>You said:</strong> "Hey Bob, {hey_bob_query}"</div>', unsafe_allow_html=True)
        
        # Get Bob's response
        with st.spinner("🤖 Bob is analyzing and preparing response..."):
            try:
                ai_response = get_ai_response(hey_bob_query)
                
                # Display Bob's response
                st.markdown(f'<div class="bob-response">🤖 <strong>Bob responds:</strong><br><br>{ai_response}</div>', unsafe_allow_html=True)
                
                # Add to conversation history
                st.session_state.conversation_history.append({
                    "user": f"Hey Bob, {hey_bob_query}",
                    "bob": ai_response,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "type": "voice"
                })
                
                # Voice response
                clean_response = ai_response.replace('"', "'").replace('\n', ' ').replace('`', '').replace('*', '').replace('#', '')
                
                voice_response_html = f"""
                <div style="text-align: center; margin: 20px 0; padding: 20px; background: #e8f5e8; border-radius: 15px;">
                    <h3 style="color: #28a745; margin-bottom: 15px;">🔊 Bob's Voice Response</h3>
                    
                    <button onclick="speakBobResponse()" style="
                        padding: 15px 30px; 
                        background: #28a745; 
                        color: white; 
                        border: none; 
                        border-radius: 10px; 
                        cursor: pointer; 
                        font-size: 18px;
                        margin: 10px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    ">🎙️ Play Response</button>
                    
                    <button onclick="restartListening()" style="
                        padding: 15px 30px; 
                        background: #007bff; 
                        color: white; 
                        border: none; 
                        border-radius: 10px; 
                        cursor: pointer; 
                        font-size: 18px;
                        margin: 10px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    ">🎤 Ask Another Question</button>
                    
                    <div id="voiceStatus" style="margin-top: 15px; font-size: 16px; color: #666;"></div>
                </div>

                <script>
                const bobResponse = `{clean_response}`;
                
                function speakBobResponse() {{
                    if ('speechSynthesis' in window) {{
                        speechSynthesis.cancel();
                        
                        const utterance = new SpeechSynthesisUtterance(bobResponse);
                        utterance.rate = 0.85;
                        utterance.pitch = 1.0;
                        utterance.volume = 1.0;
                        
                        // Set a more natural voice if available
                        const voices = speechSynthesis.getVoices();
                        const preferredVoice = voices.find(voice => 
                            voice.name.includes('Google') || 
                            voice.name.includes('Natural') || 
                            voice.lang === 'en-US'
                        );
                        if (preferredVoice) utterance.voice = preferredVoice;
                        
                        utterance.onstart = () => {{
                            document.getElementById('voiceStatus').innerHTML = '🔊 Bob is speaking...';
                        }};
                        
                        utterance.onend = () => {{
                            document.getElementById('voiceStatus').innerHTML = '✅ Response complete. Ready for next question!';
                            setTimeout(() => {{
                                document.getElementById('voiceStatus').innerHTML = '';
                            }}, 3000);
                        }};
                        
                        utterance.onerror = (event) => {{
                            document.getElementById('voiceStatus').innerHTML = '❌ Voice playback error: ' + event.error;
                        }};
                        
                        speechSynthesis.speak(utterance);
                    }} else {{
                        document.getElementById('voiceStatus').innerHTML = '❌ Text-to-speech not available in this browser';
                    }}
                }}
                
                function restartListening() {{
                    // Clear URL and restart page
                    window.location.href = window.location.pathname;
                }}
                
                // Auto-play Bob's response
                setTimeout(() => {{
                    speakBobResponse();
                }}, 1000);
                
                // Load voices (some browsers need this)
                if ('speechSynthesis' in window) {{
                    speechSynthesis.onvoiceschanged = function() {{
                        // Voices loaded
                    }};
                }}
                </script>
                """
                
                components.html(voice_response_html, height=200)
                
            except Exception as e:
                st.error(f"❌ Error getting Bob's response: {e}")

    # Manual text input for testing
    st.markdown("---")
    st.markdown("### 💬 Text Mode (For Testing)")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        manual_input = st.text_input(
            "Type to test Bob's responses:", 
            placeholder="What's the weather like today?",
            key="manual_test"
        )
    with col2:
        if st.button("Test", type="primary"):
            if manual_input:
                with st.spinner("Testing Bob..."):
                    response = get_ai_response(manual_input)
                    st.success(f"**Bob:** {response}")

    # Quick test buttons
    st.markdown("**Quick Tests:**")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Math Test"):
            response = get_ai_response("What is 15 times 7?")
            st.write(f"Bob: {response}")
    
    with col2:
        if st.button("🌍 Knowledge Test"):
            response = get_ai_response("What is the capital of Japan?")
            st.write(f"Bob: {response}")
    
    with col3:
        if st.button("📰 News Test"):
            response = get_ai_response("What's in the news today?")
            st.write(f"Bob: {response}")
    
    with col4:
        if st.button("🌤️ Weather Test"):
            response = get_ai_response("What's the weather like in New York?")
            st.write(f"Bob: {response}")

    # Instructions
    st.markdown("---")
    st.markdown("### 📋 How to Use Hey Bob")
    
    st.markdown("""
    **🎯 Step-by-Step:**
    1. **Click the microphone** to start continuous listening
    2. **Say "Hey Bob"** followed by your question
    3. **Wait for Bob's response** - he'll speak back to you!
    4. **Click "Ask Another Question"** to continue

    **🎙️ Example Commands:**
    - *"Hey Bob, what's the weather today?"*
    - *"Hey Bob, what is 25 times 4?"*
    - *"Hey Bob, tell me about artificial intelligence"*
    - *"Hey Bob, what's happening in the news?"*
    
    **⚠️ Troubleshooting:**
    - Use **Chrome browser** for best results
    - Allow **microphone permissions** when prompted
    - Speak **clearly and loudly**
    - Make sure you're on **HTTPS or localhost**
    """)

    # Conversation history
    if st.session_state.conversation_history:
        st.markdown("---")
        st.subheader("💬 Recent Conversations with Bob")
        
        for i, conv in enumerate(reversed(st.session_state.conversation_history[-5:])):
            icon = "🎙️" if conv.get('type') == 'voice' else "⌨️"
            with st.expander(f"{icon} [{conv['timestamp']}] {conv['user'][:50]}..."):
                st.markdown(f"**You:** {conv['user']}")
                st.markdown(f"**Bob:** {conv['bob']}")
        
        # Clear history
        if st.button("🗑️ Clear Conversation History"):
            st.session_state.conversation_history = []
            st.rerun()

    # System status
    st.markdown("---")
    st.markdown("### ⚙️ System Status")
    
    with st.expander("Show System Information"):
        # API Status
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**API Keys:**")
            st.write(f"- Tavily: {'✅ Configured' if TAVILY_API_KEY else '❌ Missing'}")
            st.write(f"- Google: {'✅ Configured' if GOOGLE_API_KEY else '❌ Missing'}")
        
        with col2:
            st.write("**Current URL Params:**")
            if st.query_params:
                for key, value in st.query_params.items():
                    st.write(f"- {key}: {value[:50]}...")
            else:
                st.write("- None")
        
        # Agent test
        if st.button("🧪 Test AI Agent Connection"):
            try:
                agent = get_agent()
                if agent:
                    test_response = get_ai_response("Respond with exactly: 'AI agent working perfectly'")
                    st.success(f"✅ Agent Response: {test_response}")
                else:
                    st.error("❌ Agent initialization failed")
            except Exception as e:
                st.error(f"❌ Agent test failed: {e}")

if __name__ == "__main__":
    main()
