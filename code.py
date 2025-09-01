import streamlit as st
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
import time
import json
import base64
import io
import tempfile
import os

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
    """
    agent = get_agent()
    if agent is None:
        return "Sorry, I'm having trouble connecting to my knowledge base right now."
    
    try:
        # Process through AI agent
        response = agent.run(query)
        result = response.content.strip()
        
        # Add to conversation history
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
            
        st.session_state.conversation_history.append({
            "user": query,
            "bob": result,
            "timestamp": time.strftime("%H:%M:%S"),
            "type": source_type
        })
        
        return result
        
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        return error_msg

def display_response(query, response, source_type="voice"):
    """Display the query and response."""
    
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
    
    # Voice playback
    if source_type == "voice":
        add_voice_playback(response)

def add_voice_playback(response):
    """Add voice playback functionality."""
    import streamlit.components.v1 as components
    
    # Clean response for speech
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
        ">⏹️ Stop</button>
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
            speechSynthesis.speak(utterance);
        }}
    }}
    
    function stopSpeaking() {{
        if ('speechSynthesis' in window) {{
            speechSynthesis.cancel();
        }}
    }}
    
    // Auto-play
    setTimeout(speakResponse, 1000);
    </script>
    """
    
    components.html(voice_html, height=100)

def create_voice_recorder():
    """Create a more reliable voice recorder using HTML5 MediaRecorder."""
    import streamlit.components.v1 as components
    
    recorder_html = """
    <div style="text-align: center; background: linear-gradient(135deg, #74b9ff, #0984e3); border-radius: 20px; padding: 30px; margin: 20px 0; color: white;">
        <h3>🎤 Voice Input</h3>
        <p>Click Record → Say "Hey Bob [your question]" → Click Stop</p>
        
        <div style="margin: 20px 0;">
            <button id="recordBtn" onclick="startRecording()" style="
                font-size: 50px; 
                background: rgba(255,255,255,0.2); 
                border: 3px solid white; 
                border-radius: 50%; 
                cursor: pointer; 
                padding: 20px;
                color: white;
                margin: 10px;
            ">🎤</button>
            
            <button id="stopBtn" onclick="stopRecording()" disabled style="
                font-size: 30px; 
                background: #dc3545; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                padding: 15px;
                color: white;
                margin: 10px;
            ">⏹️ Stop</button>
        </div>
        
        <div id="status" style="font-size: 18px; margin: 15px 0;">Ready to record</div>
        <div id="transcript" style="background: rgba(255,255,255,0.1); padding: 10px; border-radius: 8px; margin: 10px 0; min-height: 40px; display: none;"></div>
        
        <form id="voiceForm" method="POST" style="display: none;">
            <input type="hidden" id="voiceInput" name="voice_input" />
        </form>
    </div>

    <script>
    let mediaRecorder;
    let audioChunks = [];
    let recognition;
    let isRecording = false;

    const recordBtn = document.getElementById('recordBtn');
    const stopBtn = document.getElementById('stopBtn');
    const status = document.getElementById('status');
    const transcript = document.getElementById('transcript');

    function startRecording() {
        if (isRecording) return;
        
        // Check for speech recognition support
        if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
            status.innerHTML = '❌ Speech recognition not supported. Please use Chrome/Edge.';
            return;
        }

        isRecording = true;
        recordBtn.disabled = true;
        stopBtn.disabled = false;
        recordBtn.style.background = 'rgba(255,0,0,0.4)';
        status.innerHTML = '🎙️ Listening... Say "Hey Bob" + your question';
        transcript.style.display = 'block';
        transcript.innerHTML = 'Listening for speech...';

        // Initialize speech recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = function() {
            status.innerHTML = '👂 Listening for "Hey Bob"...';
        };

        recognition.onresult = function(event) {
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    transcript.innerHTML = 'Hearing: "' + event.results[i][0].transcript + '"';
                }
            }

            if (finalTranscript) {
                const lowerText = finalTranscript.toLowerCase();
                if (lowerText.includes('hey bob') || lowerText.includes('hi bob')) {
                    // Found wake word - process the command
                    const wakeIndex = lowerText.indexOf('hey bob') !== -1 ? lowerText.indexOf('hey bob') : lowerText.indexOf('hi bob');
                    const wakeWord = lowerText.indexOf('hey bob') !== -1 ? 'hey bob' : 'hi bob';
                    const command = finalTranscript.substring(wakeIndex + wakeWord.length).trim();
                    const fullCommand = command || finalTranscript;
                    
                    transcript.innerHTML = `✅ Processed: "${fullCommand}"`;
                    status.innerHTML = '🤖 Processing your request...';
                    
                    // Send to Streamlit
                    sendToStreamlit(fullCommand);
                    stopRecording();
                } else {
                    transcript.innerHTML = `Heard: "${finalTranscript}" (waiting for "Hey Bob")`;
                }
            }
        };

        recognition.onerror = function(event) {
            status.innerHTML = '❌ Error: ' + event.error;
            if (event.error === 'not-allowed') {
                status.innerHTML = '🔒 Microphone access denied. Please allow and refresh.';
            }
            stopRecording();
        };

        recognition.onend = function() {
            if (isRecording) {
                // Restart recognition if still recording
                setTimeout(() => {
                    if (isRecording) {
                        try {
                            recognition.start();
                        } catch (e) {
                            console.log('Recognition restart failed');
                        }
                    }
                }, 100);
            }
        };

        try {
            recognition.start();
        } catch (e) {
            status.innerHTML = '❌ Failed to start recognition: ' + e.message;
            stopRecording();
        }
    }

    function stopRecording() {
        isRecording = false;
        recordBtn.disabled = false;
        stopBtn.disabled = true;
        recordBtn.style.background = 'rgba(255,255,255,0.2)';
        
        if (recognition) {
            recognition.stop();
            recognition = null;
        }
        
        if (status.innerHTML.includes('Processing')) {
            // Keep processing message
        } else {
            status.innerHTML = 'Ready to record';
            transcript.style.display = 'none';
        }
    }

    function sendToStreamlit(query) {
        // Create a unique timestamp to force page reload
        const timestamp = new Date().getTime();
        const url = new URL(window.location);
        url.searchParams.set('voice_query', encodeURIComponent(query));
        url.searchParams.set('timestamp', timestamp);
        window.location.href = url.toString();
    }

    // Auto-stop after 15 seconds
    let autoStopTimer;
    recordBtn.addEventListener('click', () => {
        autoStopTimer = setTimeout(() => {
            if (isRecording) {
                stopRecording();
                status.innerHTML = '⏰ Auto-stopped after 15 seconds';
            }
        }, 15000);
    });

    stopBtn.addEventListener('click', () => {
        clearTimeout(autoStopTimer);
    });
    </script>
    """
    
    return components.html(recorder_html, height=350)

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
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Hey Bob - Voice Assistant</h1>
        <p>Improved Voice Recognition System</p>
    </div>
    """, unsafe_allow_html=True)

    # Process voice queries from URL
    voice_query = st.query_params.get("voice_query")
    if voice_query and not st.session_state.processing:
        st.session_state.processing = True
        
        # Clear URL params
        st.query_params.clear()
        
        try:
            import urllib.parse
            decoded_query = urllib.parse.unquote(voice_query)
        except:
            decoded_query = voice_query
        
        # Process the query
        with st.spinner("🤖 Bob is thinking..."):
            response = process_query(decoded_query, "voice")
            display_response(f"Hey Bob, {decoded_query}", response, "voice")
        
        st.session_state.processing = False
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎤 Ask Another Question", type="primary"):
                st.rerun()
        with col2:
            if st.button("🔄 Clear & Restart", type="secondary"):
                st.session_state.clear()
                st.rerun()

    # Voice Recorder Interface
    if not st.session_state.processing:
        st.markdown("### 🎙️ Voice Input")
        create_voice_recorder()

    # Show conversation history
    st.markdown("---")
    st.markdown("### 💬 Conversation")
    
    if st.session_state.conversation_history:
        last_conv = st.session_state.conversation_history[-1]
        display_response(last_conv['user'], last_conv['bob'], last_conv['type'])
    else:
        st.info("🎯 Click the microphone above and say 'Hey Bob' followed by your question!")

    # Text input fallback
    st.markdown("---")
    st.markdown("### ⌨️ Text Input (Fallback)")
    
    text_input = st.text_input("Type your question:", placeholder="What's the weather like?")
    if st.button("Send Text"):
        if text_input:
            with st.spinner("Processing..."):
                response = process_query(text_input, "text")
                display_response(text_input, response, "text")
                st.rerun()

    # Quick test buttons
    st.markdown("### 🚀 Quick Tests")
    col1, col2, col3, col4 = st.columns(4)
    
    tests = [
        ("🧮 Math", "What is 15 times 23?"),
        ("🌍 Facts", "What is the capital of Japan?"),
        ("📰 News", "Latest tech news"),
        ("🌤️ Weather", "Weather in New York")
    ]
    
    for i, (col, (label, query)) in enumerate(zip([col1, col2, col3, col4], tests)):
        with col:
            if st.button(label, key=f"test_{i}"):
                with st.spinner("Testing..."):
                    response = process_query(query, "test")
                    display_response(query, response, "test")
                    st.rerun()

    # System status
    with st.expander("⚙️ System Status"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**API Status:**")
            st.write(f"- Tavily: {'✅' if TAVILY_API_KEY else '❌'}")
            st.write(f"- Google: {'✅' if GOOGLE_API_KEY else '❌'}")
            st.write(f"- Conversations: {len(st.session_state.conversation_history)}")
        
        with col2:
            st.write("**Debug Info:**")
            st.write(f"- Processing: {st.session_state.processing}")
            st.write(f"- URL Params: {dict(st.query_params) if st.query_params else 'None'}")
            
            if st.button("🔄 Reset All"):
                st.session_state.clear()
                st.rerun()

    # Usage guide
    st.markdown("---")
    st.markdown("""
    ### 📋 How to Use
    
    **🎙️ Voice Input:**
    1. **Click the microphone** button
    2. **Say "Hey Bob"** followed by your question
    3. **Click Stop** when done speaking
    4. Wait for Bob's response
    
    **✅ This Version Fixes:**
    - Better speech recognition handling
    - More reliable JavaScript-to-Python communication
    - Proper wake word detection
    - Auto-stop after 15 seconds
    - Clearer status messages
    
    **📱 Browser Requirements:**
    - **Chrome or Edge** (required for speech recognition)
    - **Allow microphone** permissions when prompted
    - **Stable internet** connection
    
    **🔧 Troubleshooting:**
    - If voice doesn't work, use the **text input** below
    - Try **refreshing the page** if processing gets stuck
    - Use **"Reset All"** to clear any stuck states
    """)

if __name__ == "__main__":
    main()
