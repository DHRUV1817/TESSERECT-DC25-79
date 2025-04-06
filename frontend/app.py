"""
Streamlit application for the Tesseract Project
Provides a user-friendly interface for debate coaching features.
"""
import streamlit as st
import requests
import json
import pandas as pd
import time
import os
import uuid
from typing import Dict, Any

# Configuration
API_URL = "http://localhost:8000"  # FastAPI backend URL

# Page configuration
st.set_page_config(
    page_title="ELOQUENCE-AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for improved UI with professional color scheme without white
st.markdown("""
<style>
    /* Main Layout */
    .main {
        padding: 1rem 3rem;
        background-color: #1E1E2E;
        color: #CDD6F4;
    }
    
    /* Global Text Colors */
    p, li, div, span {
        color: #CDD6F4;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;  /* Increase gap between tabs */
        margin-bottom: 1rem;
        border-bottom: 1px solid #45475a;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #313244;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;  /* Increase horizontal padding */
        font-weight: 500;
        color: #CDD6F4;
        margin-right: 30px !important;  /* Increase space between tabs */
    }
    .stTabs [aria-selected="true"] {
        background-color: #89B4FA;
        color: #1E1E2E;
    }
    
    /* Highlight Text */
    .highlight {
        background-color: #F9E2AF;
        color: #1E1E2E;
        padding: 2px 4px;
        border-radius: 3px;
        font-weight: 500;
    }
    
    /* Card Styles with Non-White Colors */
    .feedback-card {
        background-color: #313244;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 5px solid #89B4FA;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    
    .evidence-item {
        background-color: #313244;
        padding: 16px;
        border-radius: 6px;
        margin-bottom: 12px;
        border-left: 4px solid #A6E3A1;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    
    .counter-card {
        background-color: #313244;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 5px solid #FAB387;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    
    .question-card {
        background-color: #313244;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 12px;
        border-left: 5px solid #CBA6F7;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        color: #CDD6F4;
    }
    
    /* Headers and Text */
    h1, h2, h3, h4, h5, h6 {
        color: #89B4FA;
    }
    
    /* Input Fields */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] div {
        background-color: #313244;
        color: #CDD6F4;
        border: 1px solid #45475a;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 700;
        color: #89B4FA;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #89B4FA;
        color: #1E1E2E;
        border: none;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        font-weight: 600;
    }
    .stButton button:hover {
        background-color: #B4BEFE;
        border: none;
    }
    
    /* Expanders */
    .st-expander {
        border-radius: 6px;
        border: 1px solid #45475a;
        background-color: #313244;
    }
    
    /* Progress Bar */
    .stProgress > div > div {
        background-color: #89B4FA;
    }
    
    /* Dataframes */
    .stDataFrame {
        background-color: #313244;
    }
    .stDataFrame [data-testid="stTable"] {
        background-color: #313244;
        color: #CDD6F4;
    }
    .stDataFrame th {
        background-color: #45475a;
        color: #CDD6F4;
    }
    
    /* Score Colors */
    .high-score {
        color: #A6E3A1;
        font-weight: bold;
    }
    .medium-score {
        color: #F9E2AF;
        font-weight: bold;
    }
    .low-score {
        color: #F38BA8;
        font-weight: bold;
    }
    
    /* About page content */
    .about-container {
        background-color: #313244;
        padding: 25px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    
    /* Success/Error Messages */
    .element-container [data-testid="stAlert"] {
        background-color: #313244;
        color: #CDD6F4;
    }
    
    /* Dividers */
    .divider {
        margin-top: 30px;
        margin-bottom: 30px;
        border-bottom: 1px solid #45475a;
    }
    
    /* Text containers */
    .text-container {
        background-color: #313244;
        padding: 20px;
        border-radius: 6px;
        border: 1px solid #45475a;
    }
</style>
""", unsafe_allow_html=True)

# Helper function for API calls
def call_api(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Call the API and return the response."""
    url = f"{API_URL}/{endpoint}"
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {}

# Display question results function with unique key prefixes
def display_socratic_questions(questions_result, prefix="socratic"):
    if not questions_result or 'questions' not in questions_result:
        st.warning("No questions available.")
        return
        
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.subheader("Socratic Questions")
    st.markdown("These questions challenge aspects of your argument and help strengthen it:")
    
    # Show argument analysis if available
    if 'argument_analysis' in questions_result:
        analysis = questions_result['argument_analysis']
        with st.expander("Argument Analysis"):
            if 'claim' in analysis and analysis['claim']:
                st.markdown(f"**Main Claim:** {analysis['claim']}")
            if 'key_terms' in analysis and analysis['key_terms']:
                st.markdown("**Key Terms:**")
                st.markdown(", ".join(analysis['key_terms']))
            if 'topic' in analysis:
                st.markdown(f"**Main Topic:** {analysis['topic']}")
            if 'structure_quality' in analysis:
                quality = analysis['structure_quality']
                quality_text = "Strong" if quality > 0.7 else ("Moderate" if quality > 0.4 else "Needs Improvement")
                st.markdown(f"**Structure Quality:** {quality_text} ({quality:.2f})")
    
    # Display questions with hints in expandable cards
    for i, question_data in enumerate(questions_result['questions']):
        st.markdown(
            f'<div class="question-card">'
            f'<strong>Q{i+1}:</strong> {question_data["question"]}'
            f'<br><em>Purpose: {question_data["purpose"]}</em>'
            f'</div>', 
            unsafe_allow_html=True
        )
        
        with st.expander("Show answer hint"):
            if "hint" in question_data:
                st.markdown(f"<div class='text-container'>{question_data['hint']}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='text-container'>Consider the assumptions, evidence, and implications related to this aspect of your argument.</div>", unsafe_allow_html=True)
            
            st.text_area(f"Your response to Q{i+1}", key=f"{prefix}_response_{i}", height=100)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# App header
st.title("ELOQUENCE-AI")
st.markdown("Improve your debate skills with AI-powered feedback and practice.")

# Navigation tabs - the tab labels include extra spaces for visual separation
tab1, tab2, tab3, tab4 = st.tabs(["Argument Analysis                     ", "Speech Analysis                     ", "Debate Practice                     ", "About                     "])

# Argument Analysis tab
with tab1:
    st.header("Argument Analysis")
    st.markdown(
        "Enter an argument to analyze its structure, logical validity, and to get suggestions for improvement."
    )
    
    argument_text = st.text_area(
        "Enter your argument:",
        height=150,
        placeholder="Example: Climate change is primarily caused by human activities because greenhouse gas emissions have increased dramatically since the industrial revolution. Multiple scientific studies have confirmed the correlation between carbon dioxide levels and global temperature rise."
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col3:
        topic = st.text_input("Topic (optional):",
                             placeholder="E.g., Climate Change, Education Reform, etc.")
    
    with col1:
        if st.button("Analyze Argument", key="analyze_btn"):
            if argument_text:
                with st.spinner("Analyzing your argument..."):
                    # Call the reasoning engine API
                    result = call_api("reasoning/analyze-argument", {
                        "text": argument_text,
                        "complexity_level": 2
                    })
                    
                    if result:
                        st.session_state.argument_result = result
                    else:
                        st.error("Failed to analyze argument. Please try again.")
            else:
                st.warning("Please enter an argument to analyze.")
                
    with col2:
        if st.button("Validate Argument", key="validate_btn"):
            if argument_text:
                with st.spinner("Validating your argument..."):
                    # Call the argument validator API
                    result = call_api("reasoning/validate-argument", {
                        "text": argument_text
                    })
                    
                    if result:
                        st.session_state.validation_result = result
                    else:
                        st.error("Failed to validate argument. Please try again.")
            else:
                st.warning("Please enter an argument to validate.")
    
    # Display analysis results
    if "argument_result" in st.session_state:
        result = st.session_state.argument_result
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.subheader("Analysis Results")
        
        # Show validity score with conditional formatting
        validity_score = result['validity_score']
        score_class = "high-score" if validity_score >= 0.7 else ("medium-score" if validity_score >= 0.4 else "low-score")
        st.markdown(f"### Argument Validity: <span class='{score_class}'>{validity_score:.2f}</span>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Argument Structure")
            st.markdown(f"**Main Claim:** {result['claim']}")
            
            st.markdown("**Evidence:**")
            if result['evidence']:
                for i, ev in enumerate(result['evidence']):
                    st.markdown(f'<div class="evidence-item">{ev}</div>', unsafe_allow_html=True)
            else:
                st.markdown("<div class='text-container'>*No clear evidence detected*</div>", unsafe_allow_html=True)
            
            if 'conclusion' in result and result['conclusion']:
                st.markdown(f"**Conclusion:** {result['conclusion']}")
            else:
                st.markdown("<div class='text-container'>**Conclusion:** *No explicit conclusion detected*</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### Reasoning Steps")
            st.markdown("<div class='text-container'>", unsafe_allow_html=True)
            for i, step in enumerate(result['reasoning_steps']):
                st.markdown(f"{i+1}. {step}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("#### Improvement Suggestions")
        for suggestion in result['improvement_suggestions']:
            st.markdown(f'<div class="feedback-card">{suggestion}</div>', unsafe_allow_html=True)
                
        # Show counterpoints
        st.markdown("#### Additional Counterarguments")
        if 'counterpoints' in result and result['counterpoints']:
            for i, counterpoint in enumerate(result['counterpoints']):
                # Skip the strongest counterpoint if already displayed
                if "strongest_counterpoint" in result and counterpoint == result['strongest_counterpoint']:
                    continue
                with st.expander(f"Counterpoint {i+1}: {counterpoint['strategy'].replace('_', ' ').title()} ({counterpoint['attack_type'].title()} Attack)"):
                    st.markdown(f'<div class="counter-card">{counterpoint["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown("<div class='text-container'>No counterpoints available for this argument.</div>", unsafe_allow_html=True)
        
        # Display rebuttal difficulty
        if "rebuttal_difficulty" in result:
            difficulty = result['rebuttal_difficulty']
            difficulty_label = "Easy" if difficulty < 0.4 else ("Moderate" if difficulty < 0.7 else "Challenging")
            difficulty_class = "high-score" if difficulty < 0.4 else ("medium-score" if difficulty < 0.7 else "low-score")
            
            st.markdown("#### Rebuttal Difficulty")
            st.progress(difficulty)
            st.markdown(f"**Level:** <span class='{difficulty_class}'>{difficulty_label} ({difficulty:.2f})</span>", unsafe_allow_html=True)
            
            if difficulty < 0.4:
                st.markdown("<div class='feedback-card'>**Tip:** This should be straightforward to rebut. Focus on strengthening your evidence.</div>", unsafe_allow_html=True)
            elif difficulty < 0.7:
                st.markdown("<div class='feedback-card'>**Tip:** This requires careful consideration. Acknowledge valid points while reasserting your position.</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='feedback-card'>**Tip:** This is challenging to rebut. You may need to concede some points while refocusing the debate.</div>", unsafe_allow_html=True)
    
    # Display Socratic questions
    if "question_result" in st.session_state:
        # Use a prefix "arg" for Argument Analysis tab
        display_socratic_questions(st.session_state.question_result, prefix="arg")

# Speech Analysis tab
with tab2:
    st.header("Speech Analysis")
    st.markdown(
        "Enter a speech transcript to analyze patterns, including filler words and hesitations."
    )
    
    transcript_text = st.text_area(
        "Enter your speech transcript:",
        height=150,
        placeholder="Example: Today I want to talk about, um, the importance of renewable energy. You know, we need to, like, find better ways to generate power because, uh, fossil fuels are limited and cause pollution."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Analyze Speech", key="analyze_speech_btn"):
            if transcript_text:
                with st.spinner("Analyzing your speech..."):
                    # Call the speech engine API
                    result = call_api("speech/analyze-transcript", {
                        "text": transcript_text
                    })
                    
                    if result:
                        st.session_state.speech_result = result
                    else:
                        st.error("Failed to analyze speech. Please try again.")
            else:
                st.warning("Please enter a speech transcript to analyze.")
                
    with col2:
        if st.button("Highlight Fillers", key="highlight_btn"):
            if transcript_text:
                with st.spinner("Highlighting filler words..."):
                    # Call the filler highlighter API
                    result = call_api("speech/highlight-fillers", {
                        "text": transcript_text
                    })
                    
                    if result:
                        st.session_state.highlight_result = result
                    else:
                        st.error("Failed to highlight fillers. Please try again.")
            else:
                st.warning("Please enter a speech transcript to highlight.")
    
    # Display speech analysis results
    if "speech_result" in st.session_state:
        result = st.session_state.speech_result
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.subheader("Speech Analysis Results")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            fluency_score = result['fluency_score']
            score_class = "high-score" if fluency_score >= 0.7 else ("medium-score" if fluency_score >= 0.4 else "low-score")
            st.markdown(f"#### Fluency Score: <span class='{score_class}'>{fluency_score:.2f}</span>", unsafe_allow_html=True)
        with col2:
            filler_count = result['filler_count']
            filler_class = "high-score" if filler_count <= 3 else ("medium-score" if filler_count <= 8 else "low-score")
            st.markdown(f"#### Filler Words: <span class='{filler_class}'>{filler_count}</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"#### Total Words: {result['word_count']}")
        with col4:
            density = result['filler_density']
            density_class = "high-score" if density <= 0.05 else ("medium-score" if density <= 0.1 else "low-score")
            st.markdown(f"#### Filler Density: <span class='{density_class}'>{density:.1%}</span>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Filler Word Analysis")
            if result['filler_breakdown']:
                filler_data = pd.DataFrame(
                    [[word, count] for word, count in result['filler_breakdown'].items()],
                    columns=["Filler Word", "Count"]
                ).sort_values("Count", ascending=False)
                
                st.dataframe(filler_data, use_container_width=True, hide_index=True)
            else:
                st.markdown("<div class='text-container'>*No filler words detected*</div>", unsafe_allow_html=True)
                
        with col2:
            st.markdown("#### Improvement Suggestions")
            for suggestion in result['improvement_suggestions']:
                st.markdown(f'<div class="feedback-card">{suggestion}</div>', unsafe_allow_html=True)
    
    # Display highlighted transcript
    if "highlight_result" in st.session_state:
        result = st.session_state.highlight_result
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.subheader("Highlighted Transcript")
        highlighted_text = result['highlighted']
        
        # Replace ** markers with HTML for highlighting
        for i in range(highlighted_text.count('**') // 2):
            highlighted_text = highlighted_text.replace('**', '<span class="highlight">', 1)
            highlighted_text = highlighted_text.replace('**', '</span>', 1)
            
        st.markdown(f'<div class="text-container">{highlighted_text}</div>', unsafe_allow_html=True)

# Debate Practice tab
with tab3:
    st.header("Debate Practice")
    st.markdown(
        "Practice debating by analyzing arguments and generating counterpoints for a given topic."
    )
    
    topic = st.text_input(
        "Debate Topic:",
        placeholder="Example: Should renewable energy be subsidized by governments?"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        stance = st.selectbox(
            "Your Stance:",
            options=["pro", "con", "neutral"],
            index=0
        )
    
    with col2:
        debate_complexity = st.selectbox(
            "Counterpoint Complexity:",
            options=["Basic (1)", "Intermediate (2)", "Advanced (3)"],
            index=1
        )
        level = int(debate_complexity.split("(")[1].split(")")[0])
    
    argument_text = st.text_area(
        "Your Argument:",
        height=150,
        placeholder="Enter your argument for the debate topic..."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Generate Counterpoints", key="counterpoint_btn"):
            if argument_text:
                with st.spinner("Generating counterpoints..."):
                    result = call_api("debate/generate-counterpoints", {
                        "argument": argument_text,
                        "topic": topic,
                        "level": level
                    })
                    
                    if result:
                        st.session_state.counterpoint_result = result
                    else:
                        st.error("Failed to generate counterpoints. Please try again.")
            else:
                st.warning("Please enter your argument to generate counterpoints.")
                
    with col2:
        if st.button("Generate Socratic Questions", key="questions_btn"):
            if argument_text:
                with st.spinner("Generating questions..."):
                    result = call_api("debate/generate-questions", {
                        "argument": argument_text,
                        "count": 3
                    })
                    
                    if result:
                        st.session_state.question_result = result
                    else:
                        st.error("Failed to generate questions. Please try again.")
            else:
                st.warning("Please enter your argument to generate questions.")
    
    # Display counterpoint results
    if "counterpoint_result" in st.session_state:
        result = st.session_state.counterpoint_result
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.subheader("Potential Counterarguments")
        
        if "strongest_counterpoint" in result:
            strongest = result["strongest_counterpoint"]
            st.markdown("#### Strongest Counterargument")
            st.markdown(f'<div class="counter-card"><strong>Strategy:</strong> {strongest["strategy"].replace("_", " ").title()} ({strongest["attack_type"].title()} Attack)<br><br>{strongest["text"]}</div>', unsafe_allow_html=True)
            
            st.markdown("#### Additional Counterarguments")
            for i, counterpoint in enumerate(result["counterpoints"]):
                if counterpoint == strongest:
                    continue
                with st.expander(f"Counterpoint {i+1}: {counterpoint['strategy'].replace('_', ' ').title()} ({counterpoint['attack_type'].title()} Attack)"):
                    st.markdown(f'<div class="counter-card">{counterpoint["text"]}</div>', unsafe_allow_html=True)

    # Display question results in the Debate Practice tab
    if "question_result" in st.session_state:
        # Use a different prefix, e.g., "debate", for unique keys here.
        display_socratic_questions(st.session_state.question_result, prefix="debate")

# About tab
with tab4:
    st.header("About Tesseract Project")
    
    st.markdown("""
    <div class="about-container">
    <h3>Overview</h3>
    
    <p>The Tesseract Project is an AI-powered debate coaching system designed to help users improve their debating skills 
    through automated feedback, argument analysis, and practice opportunities.</p>
    
    <h3>Features</h3>
    
    <ul>
      <li><strong>Argument Analysis</strong>: Evaluate the quality, structure, and logical validity of arguments</li>
      <li><strong>Speech Analysis</strong>: Detect filler words, hesitations, and other speech patterns</li>
      <li><strong>Debate Practice</strong>: Generate intelligent counterarguments for debate preparation</li>
      <li><strong>Socratic Questioning</strong>: Challenge assumptions and strengthen arguments through probing questions</li>
    </ul>
    
    <h3>How to Use</h3>
    
    <ol>
      <li><strong>Analyze Arguments</strong>: Enter any argument text to receive detailed feedback on structure, evidence, and logical validity</li>
      <li><strong>Improve Speech</strong>: Paste speech transcripts to identify patterns of filler words and get personalized suggestions</li>
      <li><strong>Practice Debating</strong>: Generate counterpoints to challenge your arguments and prepare for real debates</li>
    </ol>
    
    <h3>Development</h3>
    
    <p>This project was built with:</p>
    
    <ul>
      <li>FastAPI backend API</li>
      <li>Streamlit user interface</li>
      <li>Custom natural language processing modules</li>
    </ul>
    
    <p>The codebase is designed to be lightweight, modular, and easy to extend.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Check API Status"):
        try:
            response = requests.get(f"{API_URL}/health")
            if response.status_code == 200:
                st.success(f"API is online. Version: {response.json().get('version', 'unknown')}")
            else:
                st.error("API is offline")
        except:
            st.error("API is offline")
    
    if st.button("Check OpenAI API Status"):
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        if not openai_api_key:
            st.error("OpenAI API key not found. Enhanced AI features will be unavailable.")
        elif openai_api_key.startswith("your_") or "key_here" in openai_api_key:
            st.error("Default OpenAI API key detected. Please replace with your actual API key.")
        else:
            st.success("OpenAI API key configured. Enhanced AI features are available.")

# Run the app
if __name__ == "__main__":
    pass  # Streamlit runs the script directly
