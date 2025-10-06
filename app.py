"""
Main Application File
Streamlit-based UI for YouTube Script Generator
"""

import streamlit as st
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

# Import our modules
from config import Config
from transcript_processor import TranscriptProcessor, ProcessedTranscript
from script_generator import ScriptGenerator

# Page configuration
st.set_page_config(
    page_title="YouTube Script Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        text-align: center;
        color: #FF6B6B;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .creator-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background-color: #f8f9fa;
    }
    
    .generated-script {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    .metric-card {
        background-color: #e7f3ff;
        border-left: 5px solid #007bff;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
    }
    
    .success-message {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
    }
    
    .warning-message {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

class YouTubeScriptGeneratorApp:
    """Main application class"""
    
    def __init__(self):
        self.initialize_app()
    
    def initialize_app(self):
        """Initialize the application state"""
        
        # Initialize session state
        if 'transcripts_loaded' not in st.session_state:
            st.session_state.transcripts_loaded = False
        if 'script_generator_trained' not in st.session_state:
            st.session_state.script_generator_trained = False
        if 'available_creators' not in st.session_state:
            st.session_state.available_creators = {}
        if 'training_summary' not in st.session_state:
            st.session_state.training_summary = {}
        if 'show_script_editor' not in st.session_state:
            st.session_state.show_script_editor = False
        if 'current_script' not in st.session_state:
            st.session_state.current_script = ""
        if 'current_metadata' not in st.session_state:
            st.session_state.current_metadata = {}
        if 'original_script' not in st.session_state:
            st.session_state.original_script = ""
        
        # Initialize components
        try:
            Config.validate_config()
            self.data_dir = Config.DATA_DIR
        except Exception as e:
            st.error(f"Configuration error: {e}")
            st.stop()
    
    def run(self):
        """Run the main application"""
        
        # Header
        st.markdown('<h1 class="main-header">🎬 YouTube Script Generator</h1>', unsafe_allow_html=True)
        
        st.markdown("""
        ### Generate Authentic Hinglish YouTube Scripts
        
        This tool analyzes existing YouTube transcripts from Indian tech creators and generates 
        new scripts that match their authentic style, tone, and language patterns.
        """)
        
        # Sidebar for initialization
        with st.sidebar:
            self.render_sidebar()
        
        # Main content area
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚀 Generate Script", "✏️ Script Editor", "📊 Data Analysis", "🎭 Creator Styles", "⚙️ Settings"])
        
        with tab1:
            self.render_generation_tab()
        
        with tab2:
            if st.session_state.show_script_editor or st.session_state.current_script:
                self.render_script_editor()
            else:
                st.info("👆 Generate a script first, then you can edit it here!")
                st.markdown("""
                ### How to use the Script Editor:
                1. Generate a script using the "Generate Script" tab
                2. Click "Edit Script" button on the generated script
                3. Make your changes in the editor
                4. Save your changes or analyze the edited script
                """)
        
        with tab3:
            self.render_analysis_tab()
        
        with tab4:
            self.render_creator_styles_tab()
        
        with tab5:
            self.render_settings_tab()
    
    def render_sidebar(self):
        """Render the sidebar with initialization controls"""
        
        st.header("🔧 Setup")
        
        if not st.session_state.transcripts_loaded:
            st.markdown("**Step 1: Load Transcripts**")
            
            if st.button("📂 Load Transcript Data", type="primary"):
                with st.spinner("Loading and analyzing transcripts..."):
                    try:
                        self.load_transcripts()
                        st.session_state.transcripts_loaded = True
                        st.success("✓ Transcripts loaded successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error loading transcripts: {e}")
        else:
            st.success("✓ Transcripts loaded")
        
        if st.session_state.transcripts_loaded and not st.session_state.script_generator_trained:
            st.markdown("**Step 2: Train Generator**")
            
            if st.button("🧠 Train Script Generator", type="primary"):
                with st.spinner("Training script generator on transcript data..."):
                    try:
                        self.train_generator()
                        st.session_state.script_generator_trained = True
                        st.success("✓ Generator trained successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error training generator: {e}")
        else:
            st.success("✓ Generator trained")
        
        # Quick stats
        if st.session_state.transcripts_loaded:
            st.markdown("**📈 Quick Stats**")
            
            creator_count = len(st.session_state.available_creators)
            transcript_count = st.session_state.training_summary.get('total_transcripts', 0)
            
            st.metric("Creators Analyzed", creator_count)
            st.metric("Transcripts Processed", transcript_count)
            
            if creator_count > 0:
                avg_videos_per_creator = transcript_count / creator_count
                st.metric("Avg Videos/Creator", f"{avg_videos_per_creator:.1f}")
    
    def load_transcripts(self):
        """Load and process transcript data"""
        
        processor = TranscriptProcessor(self.data_dir)
        processed_transcripts = processor.load_all_transcripts()
        
        if not processed_transcripts:
            raise ValueError("No transcripts could be loaded")
        
        # Store in session state
        st.session_state.processed_transcripts = processed_transcripts
        st.session_state.creator_summaries = processor.get_creator_summary()
        st.session_state.available_creators = processor.get_creator_summary()
        
        print(f"Loaded {len(processed_transcripts)} transcripts")
    
    def train_generator(self):
        """Train the script generator"""
        
        processed_transcripts = st.session_state.processed_transcripts
        
        generator = ScriptGenerator()
        training_summary = generator.train_on_transcripts(processed_transcripts)
        
        # Store in session state
        st.session_state.script_generator = generator
        st.session_state.training_summary = training_summary
        
        print(f"Training completed: {training_summary}")
    
    def render_generation_tab(self):
        """Render the main script generation interface"""
        
        if not st.session_state.transcripts_loaded:
            st.info("👆 Please load transcripts first using the sidebar")
            return
        
        if not st.session_state.script_generator_trained:
            st.info("🧠 Please train the script generator first using the sidebar")
            return
        
        st.header("🚀 Generate New YouTube Script")
        
        # Generation parameters
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📝 Content Parameters")
            
            # Topic input
            topic = st.text_input(
                "Video Topic",
                placeholder="e.g., iPhone 15 Pro Max Review",
                help="Enter the main topic or product for the video"
            )
            
            # Length selection
            length_minutes = st.selectbox(
                "Video Length",
                options=[5, 8, 10, 12, 15, 18, 20, 25],
                index=2,  # Default to 10 minutes
                help="Target video duration"
            )
            
            # Content type
            content_type = st.selectbox(
                "Content Type",
                options=['review', 'comparison', 'unboxing', 'tutorial', 'general'],
                help="Type of YouTube content"
            )
            
            # Additional context
            additional_context = st.text_area(
                "Additional Context",
                placeholder="Any specific requirements, points to cover, or special instructions...",
                height=100,
                help="Optional context to guide script generation"
            )
        
        with col2:
            st.subheader("🎭 Style Parameters")
            
            # Creator style
            creator_options = ["Auto-select (best match)"] + list(st.session_state.available_creators.keys())
            creator_style = st.selectbox(
                "Creator Style",
                options=creator_options,
                help="Choose which creators style to replicate"
            )
            
            # Tone
            tone = st.selectbox(
                "Script Tone",
                options=Config.VALID_TONES,
                index=0,
                help="Overall tone and energy level"
            )
            
            # Target audience
            target_audience = st.selectbox(
                "Target Audience",
                options=Config.VALID_AUDIENCES,
                index=0,
                help="Primary audience for the script"
            )
            
            # Language mix preference
            language_mix = st.select_slider(
                "Language Mix Preference",
                options=['Hindi Heavy', 'Balanced', 'English Heavy'],
                value='Balanced',
                help="Preferred mix of Hindi and English"
            )
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                temperature = st.slider("Creativity Level", 0.1, 1.0, 0.7, 0.1)
                
            with col_b:
                max_words = st.slider("Maximum Script Length (words)", 500, 5000, 2000)
            
            force_hinglish_ascii = st.checkbox(
                "Force Hinglish (Latin script only)",
                value=True,
                help="When enabled, the model will write Hindi using Latin letters (e.g., 'aap kya kar rahe ho') to avoid Devanagari spacing issues."
            )
        
        # Generate button
        if st.button("🎬 Generate Script", type="primary"):
            if not topic:
                st.error("Please enter a video topic")
                return
            
            # Prepare parameters
            params = {
                'topic': topic,
                'length_minutes': length_minutes,
                'tone': tone,
                'target_audience': target_audience,
                'content_type': content_type,
                'creator_style': creator_style if creator_style != "Auto-select (best match)" else None,
                'additional_context': additional_context if additional_context else None
            }
            
            # Show generation progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Generating script...")
                progress_bar.progress(0.3)
                
                # Generate script
                generator = st.session_state.script_generator
                
                # Update generation config if advanced options changed
                generator.generation_config["temperature"] = temperature
                
                result = generator.generate_script(
                    **params,
                    requested_word_cap=max_words,
                    force_hinglish_ascii=force_hinglish_ascii,
                )
                
                progress_bar.progress(1.0)
                status_text.text("✓ Script generated successfully!")
                
                # Display results
                if result['success']:
                    self.display_generated_script(result)
                else:
                    st.error(f"Generation failed: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                progress_bar.progress(0)
                status_text.text("❌ Generation failed")
                st.error(f"Error generating script: {e}")
        
        # Examples section
        with st.expander("💡 Example Prompts"):
            st.markdown("""
            **For inspiration, try these topic examples:**
            
            - `Samsung Galaxy S24 Ultra vs iPhone 15 Pro Max`
            - `Top 5 Gaming Phones Under 30000`
            - `Realme GT 6 Pro Unboxing and First Look`
            - `How to Choose the Perfect Smartphone in 2024`
            - `OnePlus 12 vs Nothing Phone 2a Camera Comparison`
            
            **Pro tip:** Be specific about what you want to cover for better results!
            """)
        
        # Safety guidelines
        with st.expander("⚠️ Content Guidelines"):
            st.markdown("""
            **To avoid content blocking, please:**
            
            - Use clear, educational topics about technology
            - Avoid controversial or sensitive subjects
            - Focus on product reviews, comparisons, and tutorials
            - Keep content family-friendly and professional
            - Be specific about tech features and specifications
            
            **If generation fails:** Try rephrasing your topic or using more neutral language.
            """)
    
    def display_generated_script(self, result: Dict):
        """Display the generated script with metadata"""
        
        st.markdown("---")
        st.header("✨ Generated Script")
        
        metadata = result['metadata']
        script = result['script']
        
        # Store script in session state for editing
        st.session_state.current_script = script
        st.session_state.current_metadata = metadata
        st.session_state.original_script = script  # Store original for reset functionality
        
        # Metadata cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <strong>⏱️ Duration:</strong><br>
                {metadata['length_minutes']} minutes
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <strong>📝 Words:</strong><br>
                {metadata['estimated_word_count']:,}
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <strong>🎭 Tone:</strong><br>
                {metadata['tone_used']}
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            timing = result['timing_suggestions']
            st.markdown(f"""
            <div class="metric-card">
                <strong>⚡ Gen Time:</strong><br>
                {metadata['generation_time_seconds']}s
            </div>
            """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📁 Save Script", key="save_script_btn"):
                self.save_script_to_file(script, metadata)
        
        with col2:
            if st.button("📊 Analyze Script", key="analyze_script_btn"):
                self.analyze_script(script, metadata)
        
        with col3:
            if st.button("✏️ Edit Script", key="edit_script_btn"):
                st.session_state.show_script_editor = True
                st.rerun()
        
        with col4:
            if st.button("🔄 Generate Variation", key="variation_btn"):
                st.info("Use the generation form above with slight modifications for variation")
        
        # Script display with better formatting
        st.markdown("### 📄 Script Content")
        
        # Show full script in a scrollable container
        st.markdown("""
        <div style="
            background-color: #f8f9fa; 
            border: 1px solid #dee2e6; 
            border-radius: 8px; 
            padding: 20px; 
            max-height: 500px; 
            overflow-y: auto;
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            line-height: 1.6;
        ">
        """, unsafe_allow_html=True)
        
        st.text(script)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Timing breakdown
        with st.expander("⏰ Timing Breakdown"):
            timing_suggestions = result['timing_suggestions']
            
            st.markdown(f"""
            - **Hook:** {timing_suggestions['hook_duration']}
            - **Intro:** {timing_suggestions['intro_duration']}
            - **CTA:** Around {timing_suggestions['cta_timing']}
            - **Outro:** From {timing_suggestions['outro_timing']}
            """)
        
        # Applied patterns
        if 'creator_patterns_applied' in result and result['creator_patterns_applied']:
            with st.expander("🎯 Applied Creator Patterns"):
                patterns = result['creator_patterns_applied']
                
                cols = st.columns(2)
                with cols[0]:
                    if patterns.get('hinglish_expressions'):
                        st.write("**Hinglish Expressions:**", ", ".join(patterns['hinglish_expressions']))
                
                with cols[1]:
                    if patterns.get('engagement_phrases'):
                        st.write("**Engagement Phrases:**", ", ".join(patterns['engagement_phrases']))
    
    def render_script_editor(self):
        """Render the script editor interface"""
        
        if 'current_script' not in st.session_state:
            st.warning("No script available for editing. Please generate a script first.")
            return
        
        st.header("✏️ Script Editor")
        st.markdown("Edit your generated script and save changes in real-time.")
        
        # Editor interface
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Text area for editing
            edited_script = st.text_area(
                "Edit Script",
                value=st.session_state.current_script,
                height=400,
                help="Make your changes to the script here"
            )
            
            # Update session state with edited script
            st.session_state.current_script = edited_script
        
        with col2:
            st.subheader("📊 Live Stats")
            
            # Calculate live metrics
            word_count = len(edited_script.split())
            char_count = len(edited_script)
            estimated_minutes = word_count / 150  # Average speaking pace
            
            st.metric("Word Count", f"{word_count:,}")
            st.metric("Characters", f"{char_count:,}")
            from config import Config
            estimated_minutes = word_count / Config.SPEECH_WPM
            st.metric("Est. Duration", f"{estimated_minutes:.1f} min @ {Config.SPEECH_WPM} wpm")
            
            # Language mix analysis
            if edited_script:
                from script_validator import ScriptValidator
                validator = ScriptValidator()
                language_mix = validator._analyze_language_mix(edited_script)
                
                st.markdown("**Language Mix:**")
                st.markdown(f"Hindi: {language_mix['hindi_ratio']:.1%}")
                st.markdown(f"English: {language_mix['english_ratio']:.1%}")
                st.markdown(f"Mixed: {language_mix['mixed_ratio']:.1%}")
        
        # Action buttons for editor
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Save Changes", key="save_edited_script"):
                self.save_script_to_file(edited_script, st.session_state.current_metadata)
        
        with col2:
            if st.button("📊 Analyze Edited", key="analyze_edited_script"):
                self.analyze_script(edited_script, st.session_state.current_metadata)
        
        with col3:
            if st.button("🔄 Reset to Original", key="reset_script"):
                st.session_state.current_script = st.session_state.original_script
                st.rerun()
        
        with col4:
            if st.button("❌ Close Editor", key="close_editor"):
                st.session_state.show_script_editor = False
                st.rerun()
        
        # Show preview of edited script
        with st.expander("👀 Preview Edited Script"):
            st.markdown(edited_script.replace('\n', '\n\n'))
    
    def render_analysis_tab(self):
        """Render the data analysis tab"""
        
        if not st.session_state.transcripts_loaded:
            st.info("👆 Please load transcripts first to view analysis")
            return
        
        st.header("📊 Transcript Data Analysis")
        
        transcripts = st.session_state.processed_transcripts
        creator_summaries = st.session_state.creator_summaries
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_transcripts = len(transcripts)
            st.metric("Total Transcripts", total_transcripts)
        
        with col2:
            creator_count = len(creator_summaries)
            st.metric("Creators", creator_count)
        
        with col3:
            avg_duration = sum(t.metadata.duration for t in transcripts) / len(transcripts) / 60
            st.metric("Avg Duration", f"{avg_duration:.1f} min")
        
        with col4:
            total_words = sum(t.metadata.word_count for t in transcripts)
            st.metric("Total Words", f"{total_words:,}")
        
        # Creator breakdown
        st.subheader("🏆 Creator Breakdown")
        
        for creator, summary in creator_summaries.items():
            with st.container():
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="creator-card">
                        <h4>🎭 {creator}</h4>
                        <p><strong>Videos:</strong> {summary['video_count']} | 
                        <strong>Total Duration:</strong> {summary['total_duration'] // 60} min</p>
                        <p><strong>Language Mix:</strong> {summary['language_mix']['hindi_ratio']:.1%} Hindi, 
                        {summary['language_mix']['english_ratio']:.1%} English</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.metric("Avg Words/Video", f"{summary['total_words'] // summary['video_count']:,}")
        
        # Language analysis
        st.subheader("🗣️ Language Analysis")
        
        # Overall language distribution
        hindi_total = sum(t.language_breakdown['hindi'] for t in transcripts)
        english_total = sum(t.language_breakdown['english'] for t in transcripts)
        mixed_total = sum(t.language_breakdown['mixed'] for t in transcripts)
        total_all = hindi_total + english_total + mixed_total
        
        if total_all > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                hindi_percent = (hindi_total / total_all) * 100
                st.metric("Hindi Words", f"{hindi_percent:.1f}%")
            
            with col2:
                english_percent = (english_total / total_all) * 100
                st.metric("English Words", f"{english_percent:.1f}%")
            
            with col3:
                mixed_percent = (mixed_total / total_all) * 100
                st.metric("Mixed Words", f"{mixed_percent:.1f}%")
        
        # Tone analysis
        st.subheader("🎭 Tone Analysis")
        
        avg_enthusiasm = sum(t.tone_markers['enthusiasm'] for t in transcripts) / len(transcripts)
        avg_technical = sum(t.tone_markers['technical_depth'] for t in transcripts) / len(transcripts)
        avg_friendly = sum(t.tone_markers['friendliness'] for t in transcripts) / len(transcripts)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Avg Enthusiasm", f"{avg_enthusiasm:.1f}/10")
        
        with col2:
            st.metric("Avg Technical Detail", f"{avg_technical:.1f}/10")
        
        with col3:
            st.metric("Avg Friendliness", f"{avg_friendly:.1f}/10")
    
    def render_creator_styles_tab(self):
        """Render creator styles analysis tab"""
        
        if not st.session_state.transcripts_loaded:
            st.info("👆 Please load transcripts first to view creator styles")
            return
        
        st.header("🎭 Creator Style Analysis")
        
        creator_summaries = st.session_state.creator_summaries
        
        for creator, summary in creator_summaries.items():
            st.subheader(f"📺 {creator}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📈 Tone Profile**")
                
                enthusiasm = summary['avg_tone']['enthusiasm']
                technical = summary['avg_tone']['technical_depth']
                friendly = summary['avg_tone']['friendliness']
                
                st.metric("Enthusiasm", f"{enthusiasm:.1f}/10")
                st.metric("Technical Depth", f"{technical:.1f}/10")
                st.metric("Friendliness", f"{friendly:.1f}/10")
            
            with col2:
                st.markdown("**🗣️ Language Preferences**")
                
                hindi_ratio = summary['language_mix']['hindi_ratio']
                english_ratio = summary['language_mix']['english_ratio']
                mixed_ratio = summary['language_mix']['mixed_ratio']
                
                st.metric("Hindi Ratio", f"{hindi_ratio:.1%}")
                st.metric("English Ratio", f"{english_ratio:.1%}")
                st.metric("Mixed Ratio", f"{mixed_ratio:.1%}")
            
            # Common keywords
            if summary['common_keywords']:
                st.markdown("**🔑 Common Keywords**")
                keywords_str = ", ".join(summary['common_keywords'][:10])
                st.markdown(f"*{keywords_str}*")
            
            # Style markers
            if summary['style_markers']:
                st.markdown("**🎯 Style Markers**")
                markers_str = ", ".join(summary['style_markers'])
                st.markdown(f"*{markers_str}*")
            
            st.markdown("---")
    
    def render_settings_tab(self):
        """Render settings and configuration tab"""
        
        st.header("⚙️ Settings & Configuration")
        
        st.subheader("🔧 Current Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **📂 Data Directory:** `{Config.DATA_DIR}`  
            **🧠 Max Script Length:** {Config.MAX_SCRIPT_LENGTH_CHARS:,} characters  
            **📊 Transcripts to Load:** {Config.NUM_TRANSCRIPTS_TO_LOAD}  
            """)
        
        with col2:
            st.markdown(f"""
            **🌡️ Default Temperature:** 0.7  
            **🎭 Valid Tones:** {len(Config.VALID_TONES)} options  
            **👥 Valid Audiences:** {len(Config.VALID_AUDIENCES)} options  
            """)
        
        st.subheader("📋 Available Tones")
        
        col1, col2 = st.columns(2)
        
        with col1:
            for tone in Config.VALID_TONES[:4]:
                st.markdown(f"• {tone}")
        
        with col2:
            for tone in Config.VALID_TONES[4:]:
                st.markdown(f"• {tone}")
        
        st.subheader("👥 Target Audiences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            for audience in Config.VALID_AUDIENCES[:4]:
                st.markdown(f"• {audience}")
        
        with col2:
            for audience in Config.VALID_AUDIENCES[4:]:
                st.markdown(f"• {audience}")
        
        # Model information
        st.subheader("🤖 Model Information")
        
        st.markdown("""
        **Model Used:** Google Gemini 2.5 Flash  
        **Training Approach:** Context-aware prompting with transcript analysis  
        **Language Mix:** Automatic detection and replication  
        **Style Adaptation:** Creator-specific patterns and preferences  
        """)
        
        # Export/Import options
        st.subheader("💾 Export/Import")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📤 Export Training Data"):
                self.export_training_data()
        
        with col2:
            uploaded_file = st.file_uploader("📥 Import Training Data", type=['json'])
            if uploaded_file:
                st.info("Import functionality coming soon!")
    
    def save_script_to_file(self, script: str, metadata: Dict):
        """Save generated script to file"""
        
        # Create output directory if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = int(time.time())
        filename = f"script_{timestamp}.txt"
        filepath = output_dir / filename
        
        # Save script with metadata
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"TOPIC: {metadata['topic']}\n")
            f.write(f"DURATION: {metadata['length_minutes']} minutes\n")
            f.write(f"TONE: {metadata['tone_used']}\n")
            f.write(f"TARGET AUDIENCE: {metadata['target_audience']}\n")
            f.write(f"CONTENT TYPE: {metadata['content_type']}\n")
            f.write(f"CREATED: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            f.write(script)
        
        st.success(f"✓ Script saved to {filepath}")
    
    def analyze_script(self, script: str, metadata: Dict = None):
        """Analyze the generated script using the validator"""
        
        if not script:
            st.error("No script provided for analysis")
            return
        
        try:
            from script_validator import ScriptValidator
            
            # Get metadata or use defaults
            if metadata is None:
                metadata = st.session_state.get('current_metadata', {})
            
            target_length = metadata.get('length_minutes', 10)
            target_tone = metadata.get('tone_used', 'friendly_and_informative')
            target_audience = metadata.get('target_audience', 'general_audience')
            content_type = metadata.get('content_type', 'general')
            creator_style = metadata.get('creator_style', None)
            
            # Perform validation
            validator = ScriptValidator()
            validation_result = validator.validate_script(
                script=script,
                target_length_minutes=target_length,
                target_tone=target_tone,
                target_audience=target_audience,
                creator_style=creator_style,
                content_type=content_type
            )
            
            # Display analysis results
            self.display_script_analysis(validation_result, metadata)
            
        except Exception as e:
            st.error(f"Error analyzing script: {e}")
            st.info("Make sure the script_validator module is properly installed")
    
    def display_script_analysis(self, validation_result, metadata: Dict):
        """Display detailed script analysis results"""
        
        st.markdown("---")
        st.header("📊 Script Analysis Results")
        
        # Overall score
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            score_color = "green" if validation_result.overall_score >= 0.7 else "orange" if validation_result.overall_score >= 0.5 else "red"
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
                <h3 style="color: {score_color}; margin: 0;">Overall Score</h3>
                <h2 style="color: {score_color}; margin: 0;">{validation_result.overall_score:.2f}/1.0</h2>
                <p style="margin: 5px 0 0 0;">{'Excellent' if validation_result.overall_score >= 0.8 else 'Good' if validation_result.overall_score >= 0.6 else 'Needs Improvement'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #e7f3ff; border-radius: 8px;">
                <h3 style="color: #007bff; margin: 0;">Authenticity</h3>
                <h2 style="color: #007bff; margin: 0;">{validation_result.authenticity_score:.2f}/1.0</h2>
                <p style="margin: 5px 0 0 0;">Hinglish Quality</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #fff3cd; border-radius: 8px;">
                <h3 style="color: #856404; margin: 0;">Readability</h3>
                <h2 style="color: #856404; margin: 0;">{validation_result.readability_score:.1f}/100</h2>
                <p style="margin: 5px 0 0 0;">Ease of Reading</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            status_color = "green" if validation_result.is_valid else "red"
            status_text = "PASS" if validation_result.is_valid else "ISSUES"
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
                <h3 style="color: {status_color}; margin: 0;">Status</h3>
                <h2 style="color: {status_color}; margin: 0;">{status_text}</h2>
                <p style="margin: 5px 0 0 0;">Validation</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Detailed metrics
        st.subheader("📈 Detailed Metrics")
        
        metrics = validation_result.metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Content Metrics:**")
            st.write(f"• Word Count: {metrics['word_count']:,}")
            st.write(f"• Characters: {metrics['char_count']:,}")
            st.write(f"• Est. Duration: {metrics['estimated_minutes']:.1f} min")
            st.write(f"• Target Duration: {metrics['target_minutes']} min")
        
        with col2:
            st.markdown("**Language Analysis:**")
            lang_mix = metrics['language_mix']
            st.write(f"• Hindi: {lang_mix['hindi_ratio']:.1%}")
            st.write(f"• English: {lang_mix['english_ratio']:.1%}")
            st.write(f"• Mixed: {lang_mix['mixed_ratio']:.1%}")
            st.write(f"• Structure Score: {metrics['structure_score']:.2f}/1.0")
        
        with col3:
            st.markdown("**Quality Scores:**")
            st.write(f"• Readability: {metrics['readability_score']:.1f}/100")
            st.write(f"• Engagement: {metrics['engagement_score']}/10")
            st.write(f"• Length Deviation: {metrics['length_deviation']:.1%}")
        
        # Issues and warnings
        if validation_result.issues:
            st.subheader("🚨 Critical Issues")
            for issue in validation_result.issues:
                st.error(f"• {issue}")
        
        if validation_result.warnings:
            st.subheader("⚠️ Warnings")
            for warning in validation_result.warnings:
                st.warning(f"• {warning}")
        
        # Suggestions
        if validation_result.suggestions:
            st.subheader("💡 Improvement Suggestions")
            for suggestion in validation_result.suggestions:
                st.info(f"• {suggestion}")
        
        # Generate and display quality report
        if st.button("📋 Generate Quality Report", key="generate_report"):
            report = validator.generate_quality_report(validation_result, metadata)
            
            st.subheader("📄 Quality Report")
            st.text_area("Full Quality Report", value=report, height=300, disabled=True)
            
            # Download button for report
            st.download_button(
                label="💾 Download Report",
                data=report,
                file_name=f"script_quality_report_{int(time.time())}.txt",
                mime="text/plain"
            )
    
    def export_training_data(self):
        """Export training data for backup"""
        
        if 'script_generator' in st.session_state:
            generator = st.session_state.script_generator
            generator.save_training_context("output/training_context.json")
            st.success("✓ Training context exported to output/training_context.json")
        else:
            st.warning("No training data available to export")

# Main app execution
def main():
    """Main function to run the Streamlit app"""
    
    try:
        app = YouTubeScriptGeneratorApp()
        app.run()
        
    except Exception as e:
        st.error(f"Application error: {e}")
        st.error("Please check your configuration and try again.")

if __name__ == "__main__":
    main()

