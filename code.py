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
    
    voice_html = f"""
    <div style="text-align: center; margin: 20px 0; padding: 20px; background: #e8f5e8; border-radius: 15px;">
        <h4 style="color: #28a745; margin-bottom: 15px;">🔊 Voice Response</h4>
        
        <button onclick="speakResponse()" style="
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
        
        <button onclick="stopSpeaking()" style="
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
        
        <div id="speakStatus" style="margin-top: 10px; font-size: 14px; color: #666;"></div>
    </div>

    <script>
    const responseText = `{clean_response}`;
    
    function speakResponse() {{
        if ('speechSynthesis' in window) {{
            speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(responseText);
            utterance.rate = 0.85;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            
            // Set natural voice
            const voices = speechSynthesis.getVoices();
            const preferredVoice = voices.find(voice => 
                voice.name.includes('Google') || 
                voice.name.includes('Natural') || 
                voice.lang === 'en-US'
            );
            if (preferredVoice) utterance.voice = preferredVoice;
            
            utterance.onstart = () => {{
                document.getElementById('speakStatus').innerHTML = '🔊 Speaking...';
            }};
            
            utterance.onend = () => {{
                document.getElementById('speakStatus').innerHTML = '✅ Complete';
                setTimeout(() => {{
                    document.getElementById('speakStatus').innerHTML = '';
                }}, 2000);
            }};
            
            utterance.onerror = (event) => {{
                document.getElementById('speakStatus').innerHTML = '❌ Error: ' + event.error;
            }};
            
            speechSynthesis.speak(utterance);
        }} else {{
            document.getElementById('speakStatus').innerHTML = '❌ Speech not supported';
        }}
    }}
    
    function stopSpeaking() {{
        if ('speechSynthesis' in window) {{
            speechSynthesis.cancel();
            document.getElementById('speakStatus').innerHTML = '⏹️ Stopped';
        }}
    }}
    
    // Auto-play after 1 second
    setTimeout(speakResponse, 1000);
    </script>
    """
    
    components.html(voice_html, height=150)

def main():
    # Initialize session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'processing' not in st.session_state:
        st.session_state.processing = False

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

    # Voice Input Interface
    import streamlit.components.v1 as components
    
    voice_interface_html = """
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

    const micBtn = document.getElementById('micBtn');
    const status = document.getElementById('status');
    const transcript = document.getElementById('liveTranscript');
    const stopBtn = document.getElementById('stopBtn');

    // Check for wake word and extract command
    function checkWakeWord(text) {
        const lowerText = text.toLowerCase();
        const wakeWords = ['hey bob', 'hi bob', 'hello bob'];
        
        for (let wake of wakeWords) {
            if (lowerText.includes(wake)) {
                const wakeIndex = lowerText.indexOf(wake);
                const command = text.substring(wakeIndex + wake.length).trim();
                return command || text;
            }
        }
        return null;
    }

    // Send query to Streamlit (unified pipeline entry point)
    function sendToStreamlit(query) {
        transcript.innerHTML = `✅ Processing: "${query}"`;
        status.innerHTML = '🤖 Bob is thinking...';
        
        // Use Streamlit's query params to trigger processing
        const url = new URL(window.location);
        url.searchParams.set('voice_query', encodeURIComponent(query));
        url.searchParams.set('timestamp', Date.now());
        window.location.href = url.toString();
    }

    // Start speech recognition
    function startListening() {
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            status.innerHTML = '❌ Speech recognition not supported. Use Chrome!';
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = function() {
            isListening = true;
            micBtn.style.background = 'rgba(255,0,0,0.4)';
            micBtn.style.transform = 'scale(1.1)';
            status.innerHTML = '👂 Listening for "Hey Bob"...';
            stopBtn.style.display = 'inline-block';
            transcript.style.display = 'block';
            transcript.innerHTML = '🎧 Listening... Say "Hey Bob" + your question';
        };

        recognition.onresult = function(event) {
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcriptPart = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcriptPart;
                } else {
                    interimTranscript += transcriptPart;
                }
            }
            
            // Show live transcript
            if (interimTranscript) {
                transcript.innerHTML = `🎧 Hearing: "${interimTranscript}"`;
            }
            
            // Process final transcript
            if (finalTranscript) {
                const command = checkWakeWord(finalTranscript);
                if (command) {
                    // Wake word detected - send to unified pipeline
                    recognition.stop();
                    sendToStreamlit(command);
                } else {
                    // No wake word - continue listening
                    transcript.innerHTML = `🎧 Heard: "${finalTranscript}" (waiting for "Hey Bob")`;
                    setTimeout(() => {
                        if (isListening) {
                            transcript.innerHTML = '🎧 Listening... Say "Hey Bob" + your question';
                        }
                    }, 2000);
                }
            }
        };

        recognition.onerror = function(event) {
            if (event.error === 'not-allowed') {
                status.innerHTML = '🔒 Microphone access denied. Please refresh and allow.';
            } else if (event.error === 'no-speech') {
                // Auto-restart for continuous listening
                if (isListening) {
                    setTimeout(() => {
                        if (isListening) recognition.start();
                    }, 1000);
                }
            } else {
                status.innerHTML = `❌ Error: ${event.error}`;
            }
        };

        recognition.onend = function() {
            micBtn.style.background = 'rgba(255,255,255,0.2)';
            micBtn.style.transform = 'scale(1)';
            
            if (isListening) {
                // Auto-restart for continuous listening
                setTimeout(() => {
                    if (isListening && recognition) {
                        try {
                            recognition.start();
                        } catch (e) {
                            console.log('Recognition restart failed:', e);
                        }
                    }
                }, 100);
            } else {
                status.innerHTML = '🎤 Ready to Listen';
                stopBtn.style.display = 'none';
                transcript.style.display = 'none';
            }
        };

        recognition.start();
    }

    // Stop listening
    function stopListening() {
        isListening = false;
        if (recognition) {
            recognition.stop();
        }
        micBtn.style.background = 'rgba(255,255,255,0.2)';
        micBtn.style.transform = 'scale(1)';
        status.innerHTML = '🎤 Ready to Listen';
        stopBtn.style.display = 'none';
        transcript.style.display = 'none';
    }

    // Event listeners
    micBtn.addEventListener('click', function() {
        if (!isListening) {
            startListening();
        }
    });

    stopBtn.addEventListener('click', stopListening);
    </script>
    """

    components.html(voice_interface_html, height=300)

    # Process voice queries from URL params (unified entry point)
    voice_query = st.query_params.get("voice_query")
    if voice_query and not st.session_state.processing:
        st.session_state.processing = True
        
        # Clear URL params
        st.query_params.clear()
        
        # Process through unified pipeline
        with st.spinner("🤖 Bob is processing your request..."):
            response = process_query(voice_query, "voice")
            display_response(f"Hey Bob, {voice_query}", response, "voice")
        
        st.session_state.processing = False
        
        # Add restart button
        if st.button("🎤 Ask Another Question", type="primary"):
            st.rerun()

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

    # System Information
    with st.expander("⚙️ System Status"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**API Status:**")
            st.write(f"- Tavily: {'✅' if TAVILY_API_KEY else '❌'}")
            st.write(f"- Google: {'✅' if GOOGLE_API_KEY else '❌'}")
            st.write(f"- Conversations: {len(st.session_state.conversation_history)}")
        
        with col2:
            if st.button("🧪 Test Agent"):
                try:
                    test_response = process_query("Say exactly: 'System test successful'", "system")
                    st.success(f"✅ {test_response}")
                except Exception as e:
                    st.error(f"❌ Test failed: {e}")

    # Usage Instructions
    st.markdown("---")
    st.markdown("""
    ### 📋 How It Works
    
    **🔄 Unified Processing Pipeline:**
    1. **Voice Input:** Say "Hey Bob" + question → Speech-to-Text → Processing Pipeline
    2. **Text Input:** Type question → Direct to Processing Pipeline  
    3. **Processing:** AI Agent analyzes → Web search if needed → Generate response
    4. **Output:** Display in output window → Voice playback (for voice queries)
    
    **🎯 Features:**
    - **Wake word detection** ("Hey Bob")
    - **Continuous listening** mode
    - **Live transcript** display
    - **Unified response processing**
    - **Voice playback** of responses
    - **Conversation history**
    
    **💡 Tips:**
    - Use **Chrome** for best voice recognition
    - Speak **clearly** after "Hey Bob"
    - **Allow microphone** permissions
    - Questions appear in **output window below**
    """)

if __name__ == "__main__":
    main()
