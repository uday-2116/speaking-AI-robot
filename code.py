import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
import time
import json
import hashlib

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

def process_query(query, source_type="voice"):
    """
    Unified pipeline for processing both voice and text queries.
    This function handles the complete flow from query to response.
    """
    agent = get_agent()
    if agent is None:
        return "Sorry, I'm having trouble connecting to my knowledge base right now."
    
    try:
        # Process through AI agent
        response = agent.run(query)
        result = response.content.strip()
        
        # Add to conversation history
        st.session_state.conversation_history.append({
            "user": query,
            "bob": result,
            "timestamp": time.strftime("%H:%M:%S"),
            "type": source_type
        })
        
        return result
        
    except Exception as e:
        error_msg = f"Sorry, I encountered an error while processing your question: {str(e)}"
        return error_msg

def display_response(query, response, source_type="voice"):
    """Display the query and response in the output window."""
    
    # Display user query
    query_icon = "🎙️" if source_type == "voice" else "⌨️"
    st.markdown(f'''
    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #007bff;">
        {query_icon} <strong>You:</strong> {query}
    </div>
    ''', unsafe_allow_html=True)
    
    # Display Bob's response
    st.markdown(f'''
    <div style="background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 20px; border-radius: 15px; margin: 10px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        🤖 <strong>Bob:</strong><br><br>{response}
    </div>
    ''', unsafe_allow_html=True)
    
    # Voice playback for responses
    if source_type == "voice":
        add_voice_playback(response)

def add_voice_playback(response):
    """Add voice playback functionality for Bob's responses."""
    import streamlit.components.v1 as components
    
    # Clean response for speech synthesis
    clean_response = response.replace('"', "'").replace('\n', ' ').replace('`', '').replace('*', '').replace('#', '')
    
    # Create unique ID for this response
    response_id = hashlib.md5(clean_response.encode()).hexdigest()[:8]
    
    voice_html = f"""
    <div style="text-align: center; margin: 20px 0; padding: 20px; background: #e8f5e8; border-radius: 15px;">
        <h4 style="color: #28a745; margin-bottom: 15px;">🔊 Voice Response</h4>
        
        <button onclick="speakResponse_{response_id}()" style="
            padding: 12px 25px; 
            background: #28a745; 
            color: white; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px;
            margin: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        ">🎙️ Play Response</button>
        
        <button onclick="stopSpeaking_{response_id}()" style="
            padding: 12px 25px; 
            background: #dc3545; 
            color: white; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px;
            margin: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        ">⏹️ Stop</button>
        
        <div id="speakStatus_{response_id}" style="margin-top: 10px; font-size: 14px; color: #666;"></div>
    </div>

    <script>
    const responseText_{response_id} = `{clean_response}`;
    
    function speakResponse_{response_id}() {{
        if ('speechSynthesis' in window) {{
            speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(responseText_{response_id});
            utterance.rate = 0.85;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            
            // Wait for voices to load
            function setVoice() {{
                const voices = speechSynthesis.getVoices();
                if (voices.length > 0) {{
                    const preferredVoice = voices.find(voice => 
                        voice.name.includes('Google') || 
                        voice.name.includes('Natural') || 
                        voice.lang === 'en-US'
                    );
                    if (preferredVoice) utterance.voice = preferredVoice;
                    
                    utterance.onstart = () => {{
                        document.getElementById('speakStatus_{response_id}').innerHTML = '🔊 Speaking...';
                    }};
                    
                    utterance.onend = () => {{
                        document.getElementById('speakStatus_{response_id}').innerHTML = '✅ Complete';
                        setTimeout(() => {{
                            document.getElementById('speakStatus_{response_id}').innerHTML = '';
                        }}, 2000);
                    }};
                    
                    utterance.onerror = (event) => {{
                        document.getElementById('speakStatus_{response_id}').innerHTML = '❌ Error: ' + event.error;
                    }};
                    
                    speechSynthesis.speak(utterance);
                }} else {{
                    setTimeout(setVoice, 100);
                }}
            }}
            setVoice();
        }} else {{
            document.getElementById('speakStatus_{response_id}').innerHTML = '❌ Speech not supported';
        }}
    }}
    
    function stopSpeaking_{response_id}() {{
        if ('speechSynthesis' in window) {{
            speechSynthesis.cancel();
            document.getElementById('speakStatus_{response_id}').innerHTML = '⏹️ Stopped';
        }}
    }}
    
    // Auto-play after 1 second
    setTimeout(speakResponse_{response_id}, 1000);
    </script>
    """
    
    components.html(voice_html, height=150)

def main():
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'voice_result' not in st.session_state:
        st.session_state.voice_result = None

    # Custom CSS
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
    .voice-interface {
        background: linear-gradient(135deg, #74b9ff, #0984e3);
        border-radius: 20px;
        margin: 20px 0;
        color: white;
        padding: 30px;
        text-align: center;
    }
    .output-window {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
        border: 2px solid #e9ecef;
        min-height: 200px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Hey Bob</h1>
        <p>Streamlined Voice Assistant</p>
        <p style="font-size: 0.9rem; opacity: 0.8;">Say <span style="color: #dc3545; font-weight: bold;">"Hey Bob"</span> followed by your question</p>
    </div>
    """, unsafe_allow_html=True)

    # Voice Input Interface with Fixed JavaScript
    import streamlit.components.v1 as components
    
    voice_interface_html = f"""
    <div class="voice-interface">
        <!-- Assistant Status -->
        <div id="status" style="font-size: 20px; margin-bottom: 20px; font-weight: bold;">
            🎤 Ready to Listen
        </div>
        
        <!-- Main Microphone Button -->
        <button id="micBtn" style="
            font-size: 70px; 
            background: rgba(255,255,255,0.2); 
            border: 3px solid white; 
            border-radius: 50%; 
            cursor: pointer; 
            padding: 20px;
            transition: all 0.3s;
            color: white;
            margin-bottom: 15px;
        ">🎤</button>
        
        <!-- Live Transcript -->
        <div id="liveTranscript" style="
            background: rgba(255,255,255,0.9); 
            color: #333; 
            padding: 12px; 
            border-radius: 8px; 
            margin: 15px 0; 
            min-height: 40px;
            display: none;
            font-family: monospace;
            font-size: 14px;
        ">
            Transcript appears here...
        </div>
        
        <!-- Control Buttons -->
        <div style="margin-top: 15px;">
            <button id="stopBtn" style="
                padding: 8px 16px; 
                background: #dc3545; 
                color: white; 
                border: none; 
                border-radius: 6px; 
                cursor: pointer;
                margin: 3px;
                display: none;
            ">⏹️ Stop</button>
        </div>
    </div>

    <script>
    let recognition;
    let isListening = false;
    let recognitionTimeout;

    const micBtn = document.getElementById('micBtn');
    const status = document.getElementById('status');
    const transcript = document.getElementById('liveTranscript');
    const stopBtn = document.getElementById('stopBtn');

    // Check for wake word and extract command
    function checkWakeWord(text) {{
        const lowerText = text.toLowerCase().trim();
        const wakeWords = ['hey bob', 'hi bob', 'hello bob'];
        
        for (let wake of wakeWords) {{
            if (lowerText.includes(wake)) {{
                const wakeIndex = lowerText.indexOf(wake);
                let command = text.substring(wakeIndex + wake.length).trim();
                // If no command after wake word, return the full text
                return command || text.substring(wakeIndex + wake.length).trim() || "Hello";
            }}
        }}
        return null;
    }}

    // Send query to Streamlit using session state approach
    function sendToStreamlit(query) {{
        transcript.innerHTML = `✅ Processing: "${{query}}"`;
        status.innerHTML = '🤖 Bob is thinking...';
        
        // Use Streamlit's experimental approach for JavaScript to Python communication
        // Store in a hidden element that can be read by Streamlit
        let hiddenInput = document.getElementById('voiceResult');
        if (!hiddenInput) {{
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.id = 'voiceResult';
            document.body.appendChild(hiddenInput);
        }}
        hiddenInput.value = query;
        
        // Trigger a custom event
        const event = new CustomEvent('voiceProcessed', {{ 
            detail: {{ query: query, timestamp: Date.now() }} 
        }});
        document.dispatchEvent(event);
        
        // Also try URL approach as backup
        const url = new URL(window.location);
        url.searchParams.set('voice_query', encodeURIComponent(query));
        url.searchParams.set('timestamp', Date.now());
        window.location.href = url.toString();
    }}

    // Initialize speech recognition with better error handling
    function initSpeechRecognition() {{
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {{
            status.innerHTML = '❌ Speech recognition not supported. Please use Chrome or Edge!';
            micBtn.disabled = true;
            return null;
        }}

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const rec = new SpeechRecognition();
        
        rec.continuous = false; // Changed to false for better reliability
        rec.interimResults = true;
        rec.lang = 'en-US';
        rec.maxAlternatives = 1;

        rec.onstart = function() {{
            isListening = true;
            micBtn.style.background = 'rgba(255,0,0,0.4)';
            micBtn.style.transform = 'scale(1.1)';
            status.innerHTML = '👂 Listening for "Hey Bob"...';
            stopBtn.style.display = 'inline-block';
            transcript.style.display = 'block';
            transcript.innerHTML = '🎧 Listening... Say "Hey Bob" + your question';
            
            // Set timeout for automatic stop
            recognitionTimeout = setTimeout(() => {{
                if (isListening && rec) {{
                    rec.stop();
                }}
            }}, 10000); // 10 seconds timeout
        }};

        rec.onresult = function(event) {{
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
            const currentText = finalTranscript || interimTranscript;
            if (currentText) {{
                transcript.innerHTML = `🎧 Hearing: "${{currentText}}"`;
                
                // Check for wake word in real-time
                const command = checkWakeWord(currentText);
                if (command && finalTranscript) {{
                    // Wake word detected with final transcript
                    clearTimeout(recognitionTimeout);
                    rec.stop();
                    sendToStreamlit(command);
                    return;
                }}
            }}
        }};

        rec.onerror = function(event) {{
            console.error('Speech recognition error:', event.error);
            clearTimeout(recognitionTimeout);
            
            if (event.error === 'not-allowed') {{
                status.innerHTML = '🔒 Microphone access denied. Please refresh and allow.';
            }} else if (event.error === 'no-speech') {{
                status.innerHTML = '🔇 No speech detected. Try again.';
            }} else if (event.error === 'network') {{
                status.innerHTML = '🌐 Network error. Check your connection.';
            }} else {{
                status.innerHTML = `❌ Error: ${{event.error}}`;
            }}
            
            stopListening();
        }};

        rec.onend = function() {{
            clearTimeout(recognitionTimeout);
            stopListening();
        }};

        return rec;
    }}

    // Start listening
    function startListening() {{
        if (isListening) return;
        
        recognition = initSpeechRecognition();
        if (!recognition) return;
        
        try {{
            recognition.start();
        }} catch (e) {{
            console.error('Failed to start recognition:', e);
            status.innerHTML = '❌ Failed to start listening. Try again.';
            stopListening();
        }}
    }}

    // Stop listening
    function stopListening() {{
        isListening = false;
        clearTimeout(recognitionTimeout);
        
        if (recognition) {{
            try {{
                recognition.stop();
            }} catch (e) {{
                console.error('Error stopping recognition:', e);
            }}
            recognition = null;
        }}
        
        micBtn.style.background = 'rgba(255,255,255,0.2)';
        micBtn.style.transform = 'scale(1)';
        status.innerHTML = '🎤 Ready to Listen';
        stopBtn.style.display = 'none';
        transcript.style.display = 'none';
    }}

    // Event listeners
    micBtn.addEventListener('click', function() {{
        if (!isListening) {{
            startListening();
        }}
    }});

    stopBtn.addEventListener('click', stopListening);
    
    // Handle page visibility changes
    document.addEventListener('visibilitychange', function() {{
        if (document.hidden && isListening) {{
            stopListening();
        }}
    }});
    </script>
    """

    components.html(voice_interface_html, height=300)

    # Process voice queries from URL params (primary method)
    voice_query = st.query_params.get("voice_query")
    if voice_query and not st.session_state.processing:
        st.session_state.processing = True
        
        # Clear URL params to prevent re-processing
        st.query_params.clear()
        
        # Decode the query
        try:
            decoded_query = voice_query
            st.session_state.voice_result = decoded_query
        except:
            decoded_query = voice_query
        
        # Process through unified pipeline
        with st.spinner("🤖 Bob is processing your request..."):
            response = process_query(decoded_query, "voice")
            display_response(f"Hey Bob, {decoded_query}", response, "voice")
        
        st.session_state.processing = False
        
        # Add restart button
        if st.button("🎤 Ask Another Question", type="primary"):
            st.rerun()

    # Alternative: Check for voice result in session state
    elif st.session_state.voice_result and not st.session_state.processing:
        st.session_state.processing = True
        query = st.session_state.voice_result
        st.session_state.voice_result = None
        
        with st.spinner("🤖 Bob is processing your request..."):
            response = process_query(query, "voice")
            display_response(f"Hey Bob, {query}", response, "voice")
        
        st.session_state.processing = False

    # Output Window (Below Voice Interface)
    st.markdown("---")
    st.markdown("### 💬 Conversation Output")
    
    output_container = st.container()
    with output_container:
        # Show recent conversation or placeholder
        if st.session_state.conversation_history:
            # Show last conversation
            last_conv = st.session_state.conversation_history[-1]
            display_response(last_conv['user'], last_conv['bob'], last_conv['type'])
        else:
            st.markdown('''
            <div class="output-window">
                <div style="text-align: center; color: #6c757d; padding: 40px;">
                    <h4>🎯 Ready for Your First Question</h4>
                    <p>Click the microphone above and say "Hey Bob" followed by your question.<br>
                    Your conversation will appear here.</p>
                    
                    <div style="margin: 20px 0; padding: 15px; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">
                        <strong>⚠️ Troubleshooting Tips:</strong><br>
                        • Use <strong>Chrome or Edge</strong> browser<br>
                        • Allow <strong>microphone permissions</strong><br>
                        • Speak clearly after "Hey Bob"<br>
                        • Check your internet connection<br>
                        • If issues persist, try the text input below
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

    # Manual Text Input (Alternative Entry Point)
    st.markdown("---")
    st.markdown("### ⌨️ Text Mode (Alternative Input)")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        manual_input = st.text_input(
            "Type your question:", 
            placeholder="What's the weather like today?",
            key="manual_input"
        )
    with col2:
        if st.button("Send", type="primary"):
            if manual_input:
                # Process through same unified pipeline
                with st.spinner("🤖 Processing..."):
                    response = process_query(manual_input, "text")
                    display_response(manual_input, response, "text")
                    st.rerun()

    # Quick Test Buttons
    st.markdown("**🚀 Quick Tests:**")
    col1, col2, col3, col4 = st.columns(4)
    
    test_queries = [
        ("📊 Math", "What is 23 times 15?"),
        ("🌍 Knowledge", "What is the largest ocean?"),
        ("📰 News", "What's happening in tech news today?"),
        ("🌤️ Weather", "Weather forecast for San Francisco")
    ]
    
    for i, (col, (label, query)) in enumerate(zip([col1, col2, col3, col4], test_queries)):
        with col:
            if st.button(label, key=f"test_{i}"):
                with st.spinner("Testing..."):
                    response = process_query(query, "test")
                    display_response(query, response, "test")
                    st.rerun()

    # Conversation History
    if len(st.session_state.conversation_history) > 1:
        st.markdown("---")
        st.markdown("### 📜 Recent Conversations")
        
        with st.expander(f"Show {len(st.session_state.conversation_history)} previous conversations"):
            for i, conv in enumerate(reversed(st.session_state.conversation_history[:-1])):
                icon = "🎙️" if conv['type'] == 'voice' else "⌨️" if conv['type'] == 'text' else "🧪"
                st.markdown(f"**{icon} [{conv['timestamp']}] You:** {conv['user']}")
                st.markdown(f"**🤖 Bob:** {conv['bob']}")
                st.markdown("---")
        
        if st.button("🗑️ Clear History"):
            st.session_state.conversation_history = []
            st.rerun()

    # System Information & Debugging
    with st.expander("⚙️ System Status & Debug"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**API Status:**")
            st.write(f"- Tavily: {'✅' if TAVILY_API_KEY else '❌'}")
            st.write(f"- Google: {'✅' if GOOGLE_API_KEY else '❌'}")
            st.write(f"- Conversations: {len(st.session_state.conversation_history)}")
            
            if st.button("🧪 Test Agent"):
                try:
                    test_response = process_query("Say exactly: 'System test successful'", "system")
                    st.success(f"✅ {test_response}")
                except Exception as e:
                    st.error(f"❌ Test failed: {e}")
        
        with col2:
            st.write("**Debug Info:**")
            st.write(f"- Processing: {st.session_state.processing}")
            st.write(f"- Voice Result: {st.session_state.voice_result}")
            st.write(f"- URL Params: {dict(st.query_params)}")
            
            if st.button("🔄 Reset Session"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

    # Usage Instructions
    st.markdown("---")
    st.markdown("""
    ### 📋 How It Works & Troubleshooting
    
    **🔄 Improved Voice Processing Pipeline:**
    1. **Voice Input:** Say "Hey Bob" + question → Enhanced Speech-to-Text → Processing Pipeline
    2. **Text Input:** Type question → Direct to Processing Pipeline  
    3. **Processing:** AI Agent analyzes → Web search if needed → Generate response
    4. **Output:** Display in output window → Voice playback (for voice queries)
    
    **🎯 Key Fixes Applied:**
    - **Better Error Handling:** Improved recognition timeout and error recovery
    - **Dual Communication:** URL params + session state for reliability  
    - **Browser Compatibility:** Enhanced support for Chrome/Edge
    - **Unique Voice IDs:** Prevents JavaScript conflicts
    - **Automatic Restart:** Better session management
    
    **🚨 Common Issues & Solutions:**
    
    **Voice Recognition Not Working:**
    - ✅ Use **Chrome or Edge** browser (Safari/Firefox have limited support)
    - ✅ **Allow microphone permissions** when prompted
    - ✅ Check your **internet connection** (speech recognition requires online access)
    - ✅ Speak **clearly and loudly** after "Hey Bob"
    - ✅ Wait for the red microphone indicator before speaking
    
    **Processing Stuck:**
    - ✅ Use the **"Reset Session"** button in System Status
    - ✅ Try **refreshing the page**
    - ✅ Use **text input** as alternative
    - ✅ Check **System Status** for API connectivity
    
    **💡 Best Practices:**
    - Start with **"Hey Bob"** clearly, then pause briefly
    - Speak **conversationally** but clearly
    - Keep questions **concise and specific**
    - Use the **text mode** for complex or long queries
    """)

if __name__ == "__main__":
    main()
