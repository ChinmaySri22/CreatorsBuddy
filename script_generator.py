"""
Script Generator Module
Uses Google Gemini API to generate YouTube scripts based on transcript analysis
"""

import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
import json
import tiktoken
from typing import Dict
import time
from config import Config
from transcript_processor import ProcessedTranscript

class ScriptGenerator:
    """Main script generation class using Gemini API"""
    
    def __init__(self):
        """Initialize the script generator with Gemini configuration"""
        self.api_key = Config.GEMINI_API_KEY
        genai.configure(api_key=self.api_key)
        
        # Initialize Gemini models
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,  # Safer default; per-call overrides based on target length
        }
        
        # Safety settings to reduce blocking
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash',
            safety_settings=self.safety_settings
        )
        
        # Training data cache
        self.training_context = {}
        self.creator_styles = {}
        
        print("+ Script Generator initialized with Gemini API")
    
    def train_on_transcripts(self, processed_transcripts: List[ProcessedTranscript]) -> Dict[str, any]:
        """Train/initialize the system with transcript data"""
        print("Training script generator on transcript data...")
        
        # Analyze creator styles
        self.creator_styles = self._analyze_creator_styles(processed_transcripts)
        
        # Create training prompts and examples
        self.training_context = self._create_training_context(processed_transcripts)
        
        # Test generation with sample
        sample_result = self._test_generation()
        
        training_summary = {
            'total_transcripts': len(processed_transcripts),
            'creators_analyzed': len(self.creator_styles),
            'training_examples': len(self.training_context.get('examples', [])),
            'sample_generation_success': sample_result['success']
        }
        
        print(f"[OK] Training completed: {training_summary}")
        return training_summary
    
    def _analyze_creator_styles(self, transcripts: List[ProcessedTranscript]) -> Dict[str, Dict]:
        """Analyze and extract unique styles from each creator"""
        creator_analysis = {}
        
        for transcript in transcripts:
            creator = transcript.metadata.uploader
            
            if creator not in creator_analysis:
                creator_analysis[creator] = {
                    'transcripts': [],
                    'common_patterns': set(),
                    'language_preferences': {'hindi_dominant': 0, 'english_dominant': 0, 'balanced': 0},
                    'tone_profile': {'enthusiasm': 0, 'technical_depth': 0, 'friendliness': 0},
                    'content_style': set(),
                    'intro_patterns': [],
                    'outro_patterns': []
                }
            
            analysis = creator_analysis[creator]
            analysis['transcripts'].append(transcript)
            
            # Analyze language preferences
            lang_mix = transcript.language_breakdown
            if lang_mix['hindi_ratio'] > 0.6:
                analysis['language_preferences']['hindi_dominant'] += 1
            elif lang_mix['english_ratio'] > 0.6:
                analysis['language_preferences']['english_dominant'] += 1
            else:
                analysis['language_preferences']['balanced'] += 1
            
            # Analyze tone profile
            for tone in ['enthusiasm', 'technical_depth', 'friendliness']:
                analysis['tone_profile'][tone] += transcript.tone_markers[tone]
            
            # Extract style markers
            analysis['content_style'].update(transcript.creator_style.get('style_markers', []))
            
            # Analyze intro/outro patterns
            intro_segments = transcript.segments[:5]  # First 5 segments
            outro_segments = transcript.segments[-5:]  # Last 5 segments
            
            analysis['intro_patterns'].extend([s['text'] for s in intro_segments if s.get('text')])
            analysis['outro_patterns'].extend([s['text'] for s in outro_segments if s.get('text')])
        
        # Normalize creator analysis
        for creator, analysis in creator_analysis.items():
            transcript_count = len(analysis['transcripts'])
            
            # Normalize tone profile
            for tone in analysis['tone_profile']:
                analysis['tone_profile'][tone] /= transcript_count
            
            # Convert sets to lists for serialization
            analysis['common_patterns'] = list(analysis['common_patterns'])
            analysis['content_style'] = list(analysis['content_style'])
            
            # Deduplicate patterns
            analysis['intro_patterns'] = list(set(analysis['intro_patterns'][:10]))
            analysis['outro_patterns'] = list(set(analysis['outro_patterns'][:10]))
        
        return creator_analysis
    
    def _create_training_context(self, transcripts: List[ProcessedTranscript]) -> Dict:
        """Create training context and examples for Gemini"""
        # Organize examples by creator and style
        examples_by_creator = {}
        
        for transcript in transcripts:
            creator = transcript.metadata.uploader
            
            if creator not in examples_by_creator:
                examples_by_creator[creator] = []
            
            # Create training example
            example = {
                'title': transcript.metadata.title,
                'creator': creator,
                'style_summary': {
                    'tone_markers': transcript.tone_markers,
                    'language_mix': transcript.language_breakdown,
                    'title_type': self._analyze_title_type(transcript.metadata.title),
                    'duration_category': self._categorize_duration(transcript.metadata.duration)
                },
                'sample_content': transcript.clean_text[:2000],  # First 2000 chars
                'key_patterns': transcript.keywords[:10]
            }
            
            examples_by_creator[creator].append(example)
        
        # Create training prompts
        training_prompts = self._generate_training_prompts(examples_by_creator)
        
        return {
            'examples_by_creator': examples_by_creator,
            'training_prompts': training_prompts,
            'style_guidelines': self._create_style_guidelines()
        }
    
    def _analyze_title_type(self, title: str) -> str:
        """Analyze the type of video based on title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['review', 'रीव्यू', 'test', 'टेस्ट']):
            return 'review'
        elif any(word in title_lower for word in ['vs', 'versus', 'कंपेयर', 'comparison']):
            return 'comparison'
        elif any(word in title_lower for word in ['unboxing', 'अनबॉक्सिंग', 'first look']):
            return 'unboxing'
        elif any(word in title_lower for word in ['guide', 'गाइड', 'tips', 'how to']):
            return 'tutorial'
        else:
            return 'general'
    
    def _categorize_duration(self, duration_seconds: int) -> str:
        """Categorize video duration"""
        duration_minutes = duration_seconds // 60
        
        if duration_minutes <= 5:
            return 'short'
        
        return 'medium'
    
    def _generate_training_prompts(self, examples_by_creator: Dict) -> List[Dict]:
        """Generate context-aware training prompts"""
        prompts = []
        
        for creator, examples in examples_by_creator.items():
            if len(examples) > 0:
                # Create creator-specific prompt
                creator_prompt = self._create_creator_specific_prompt(creator, examples[0])
                prompts.append(creator_prompt)
        
        return prompts
    
    def _create_creator_specific_prompt(self, creator: str, example: Dict) -> Dict:
        """Create a prompt specific to a creator's style"""
        
        # Base system prompt
        base_prompt = f"""You are generating YouTube scripts in the style of {creator}, a popular Hinglish (Hindi + English) tech YouTuber. 

Creator Style Guidelines for {creator}:
"""
        
        # Add creator-specific guidelines based on analysis
        if 'trakin' in creator.lower():
            base_prompt += """
- Use enthusiastic and energetic tone
- Mix Hindi and English naturally (Hinglish)
- Focus on smartphone reviews and comparisons
- Include detailed specifications and pricing
- Use expressions like "दोस्तों" frequently
- Include call-to-action for likes and subscriptions
- Structure: Hook intro -> Product overview -> Detailed review -> Pricing -> Conclusion
"""
        elif 'techbar' in creator.lower():
            base_prompt += """
- Use friendly and informative tone
- Provide comprehensive technical analysis
- Longer form content structure
- Professional yet approachable language style
- Detailed comparisons and features breakdown
- Include real-world usage scenarios
"""
        else:
            base_prompt += """
- Maintain engaging tech content style
- Mix conversational Hindi and English
- Focus on technology reviews and guides
- Include practical insights and comparisons
"""
        
        base_prompt += f"""

Generate authentic YouTube scripts that:
1. Match {creator}'s speaking patterns and style
2. Use appropriate Hinglish mix
3. Include engaging elements like hooks, transitions, and CTAs
4. Are structured for {example['style_summary']['duration_category']}-length videos
5. Capture the creator's unique voice and personality

Remember: The script should sound like {creator} actually wrote and spoke it - authentic and natural."""

        return {
            'creator': creator,
            'type': 'creator_specific',
            'prompt': base_prompt,
            'example': example
        }
    
    def _create_style_guidelines(self) -> Dict[str, str]:
        """Create general style guidelines for script generation"""
        return {
            'hinglish_patterns': {
                'common_transitions': ['अब देखते हैं', 'तो यहाँ पर', 'बात यह है कि', 'अब मुख्य बात'],
                'engagement_phrases': ['दोस्तों', 'भाई', 'यार', 'आपको पता है', 'सुनने के लिए'],
                'technical_mix': ['इसके में फीचर्स हैं', 'स्पेक्स देखिए', 'परफॉर्मेंस बहुत अच्छा है']
            },
            'script_structure': {
                'hook': 'Start with engaging question or statement',
                'intro': 'Brief intro with channel branding',
                'main_content': 'Core review/content with logical flow',
                'cta': 'Call to action for engagement',
                'outro': 'Channel promotion and subscription reminder'
            },
            'content_types': {
                'review': 'Focus on detailed analysis, pros/cons, recommendations',
                'comparison': 'Side-by-side comparison with clear winner',
                'unboxing': 'Step-by-step unboxing with reactions',
                'tutorial': 'Clear instructions with visual cues',
                'general': 'Balanced informative and entertaining content'
            }
        }
    
    def _test_generation(self) -> Dict[str, any]:
        """Test generation capability with a sample prompt"""
        try:
            test_prompt = """Generate a 2-minute YouTube script intro for a smartphone review video in Hinglish style used by Indian tech YouTubers."""
            
            response = self.model.generate_content(
                test_prompt,
                generation_config=self.generation_config
            )
            
            return {
                'success': True,
                'sample_length': len(response.text) if response.text else 0,
                'response_preview': response.text[:200] if response.text else 'No content generated'
            }
            
        except Exception as e:
            print(f"Test generation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_script(self, 
                       topic: str,
                       length_minutes: int,
                       tone: str,
                       target_audience: str,
                       content_type: str,
                       creator_style: Optional[str] = None,
                       additional_context: Optional[str] = None,
                       requested_word_cap: Optional[int] = None,
                       force_hinglish_ascii: bool = True) -> Dict[str, any]:
        """Generate a YouTube script based on parameters"""
        
        print(f"Generating script: {topic} ({length_minutes} min, {tone}, {target_audience})")
        
        try:
            start_time = time.time()
            
            # Determine hard word cap
            default_target_words = max(150, int(length_minutes * 150))
            if requested_word_cap and requested_word_cap > 0:
                hard_word_cap = max(200, min(5000, int(requested_word_cap)))
            else:
                # Default: cap at min(target words, 2000)
                hard_word_cap = min(2000, default_target_words)
            
            # Build prompt reflecting the exact cap
            prompt = self._build_generation_prompt(
                topic, length_minutes, tone, target_audience,
                content_type, creator_style, additional_context, hard_word_cap,
                force_hinglish_ascii=force_hinglish_ascii
            )

            # Compute a safe per-call token cap based on desired word count (~1.3 tokens/word)
            approx_tokens = int(hard_word_cap * 1.3)  # rough tokens-per-word multiplier
            call_generation_config = {**self.generation_config, "max_output_tokens": max(256, min(4096, approx_tokens))}
            
            # Try generation with full prompt first
            response = self.model.generate_content(
                prompt,
                generation_config=call_generation_config
            )
            
            generation_time = time.time() - start_time
            
            # Check for safety issues
            if not response.candidates:
                # Try with a simpler, safer prompt
                print("First attempt blocked, trying with simpler prompt...")
                simple_prompt = f"""Create a COMPLETE {length_minutes}-minute YouTube script about {topic} in Hinglish (Hindi + English mix). 
                Make it educational, family-friendly, and suitable for tech enthusiasts. 
                Include: Introduction, main content about {topic}, and conclusion with call-to-action.
                Keep it professional and informative.
                IMPORTANT: Generate the ENTIRE script from start to finish. Do not truncate or cut off mid-sentence."""
                
                response = self.model.generate_content(
                    simple_prompt,
                    generation_config=call_generation_config
                )
                
                if not response.candidates or not response.text:
                    return {
                        'success': False,
                        'error': 'Content blocked by safety filters. Please try a different topic or rephrase your request.',
                        'metadata': {'topic': topic, 'length_minutes': length_minutes}
                    }
            
            # Check safety ratings safely
            if getattr(response, 'candidates', None):
                candidate = response.candidates[0]
                if getattr(candidate, 'safety_ratings', None):
                    blocked_categories = []
                    for rating in candidate.safety_ratings:
                        if getattr(rating, 'probability', None) in ['HIGH', 'MEDIUM']:
                            blocked_categories.append(f"{rating.category}: {rating.probability}")
                    if blocked_categories:
                        return {
                            'success': False,
                            'error': f'Content blocked by safety filters: {", ".join(blocked_categories)}. Try rephrasing your topic or context.',
                            'metadata': {'topic': topic, 'length_minutes': length_minutes}
                        }

            # Extract text safely
            script_text = self._extract_text_from_response(response)
            if not script_text:
                return {
                    'success': False,
                    'error': 'No text content generated. The response may have been blocked or filtered.',
                    'metadata': {'topic': topic, 'length_minutes': length_minutes}
                }
            
            # Continuation if early stop or short vs cap
            accumulated_text = script_text
            needs_more = len(accumulated_text.split()) < int(hard_word_cap * 0.85)
            expected_items = self._extract_expected_item_count(topic, additional_context)
            if expected_items:
                current_items = self._count_list_items(accumulated_text)
                if current_items < expected_items:
                    needs_more = True
            if needs_more:
                # first generic continuation
                accumulated_text = self._attempt_continuation(accumulated_text, hard_word_cap, call_generation_config)
                # guided continuation for remaining items
                if expected_items:
                    current_items = self._count_list_items(accumulated_text)
                    if current_items < expected_items and (hard_word_cap - len(accumulated_text.split())) > 60:
                        guidance = f"Continue with items {current_items+1} to {expected_items}. Keep each item concise and balanced. Do not repeat. "
                        accumulated_text = self._attempt_guided_continuation(accumulated_text, hard_word_cap, call_generation_config, guidance)

            # Clean and post-process the generated script
            cleaned_text = self._clean_response_text(accumulated_text)
            processed_script = self._post_process_script(cleaned_text, length_minutes, hard_word_cap)
            
            return {
                    'success': True,
                    'script': processed_script['script'],
                    'metadata': {
                        'topic': topic,
                        'length_minutes': length_minutes,
                        'estimated_word_count': processed_script['word_count'],
                        'estimated_speaking_time': processed_script['speaking_time'],
                        'tone_used': tone,
                        'target_audience': target_audience,
                        'content_type': content_type,
                        'creator_style_used': creator_style,
                        'generation_time_seconds': round(generation_time, 2)
                    },
                    'timing_suggestions': processed_script['timing_suggestions'],
                    'creator_patterns_applied': processed_script['pattern_markers']
                }
                
        except Exception as e:
            print(f"Script generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'metadata': {'topic': topic, 'length_minutes': length_minutes}
            }
    
    def _build_generation_prompt(self, 
                                topic: str, 
                                length_minutes: int, 
                                tone: str, 
                                target_audience: str,
                                content_type: str,
                                creator_style: Optional[str],
                                additional_context: Optional[str],
                                hard_word_cap: Optional[int] = None,
                                force_hinglish_ascii: bool = True) -> str:
        """Build comprehensive prompt for script generation"""
        
        # Base prompt structure
        prompt_parts = []
        
        # System context
        prompt_parts.append("""You are an expert YouTube script writer specializing in creating authentic Hinglish (Hindi + English mix) content for Indian tech channels. Create educational, informative, and family-friendly content about technology, gadgets, and reviews.""")
        
        # Style context from creator analysis
        if creator_style and creator_style in self.creator_styles:
            creator_data = self.creator_styles[creator_style]
            prompt_parts.append(f"\nCREATOR STYLE CONTEXT - Replicate the style of {creator_style}:")
            prompt_parts.append(f"- Language preferences: {self._get_language_mix_description(creator_data)}")
            prompt_parts.append(f"- Tone profile: {self._get_tone_description(creator_data)}")
            prompt_parts.append(f"- Content style: Natural conversational tone")
        
        # Main instruction
        target_words = max(150, int(length_minutes * 150))
        if hard_word_cap is None:
            hard_word_cap = min(2000, target_words)
        prompt_parts.append(f"""
SCRIPT REQUIREMENTS:
- Topic: {topic}
- Duration: {length_minutes} minutes (approximately {length_minutes * Config.SPEECH_WPM} words)
- Tone: {tone}
- Target Audience: {target_audience}
- Content Type: {content_type}

IMPORTANT HARD LIMIT: Write no more than {hard_word_cap} words. Stop before exceeding this word cap. The script must be complete but concise.
IMPORTANT: Generate a COMPLETE script from start to finish, but keep it within the word cap. Do not cut off mid-sentence. Include all sections: Hook, Introduction, Main Content, and Conclusion with Call-to-Action.
""")
        
        # Style guidelines
        tone_description = self._get_tone_guidelines(tone)
        content_guidelines = self._get_content_type_guidelines(content_type)
        
        prompt_parts.append(f"""
STYLE GUIDELINES:
{tone_description}

{content_guidelines}

SCRIPT STRUCTURE:
1. Hook (0-15 seconds): Engaging opening question or statement
2. Intro (15-30 seconds): Channel greeting and video preview
3. Main Content ({length_minutes - 1}-{length_minutes - 0.5} minutes): Core topic discussion
4. Call-to-Action (15-30 seconds): Like, subscribe, notification bell
5. Outro (15-30 seconds): Channel promotion and preview

HINGLISH LANGUAGE PATTERNS:
- Natural mix of Hindi and English
- Common phrases: "दोस्तों", "भाई", "तो यहाँ पर", "सुनिए"
- Technical terms in English, explanations in Hindi
- Engaging expressions and enthusiasm markers
""")
        
        if additional_context:
            prompt_parts.append(f"\nADDITIONAL CONTEXT:\n{additional_context}")
        
        if force_hinglish_ascii:
            prompt_parts.append("\nIMPORTANT: Write in Hinglish using Latin letters only (no Devanagari). Example: 'aap kya kar rahe ho', 'dosto', 'performance'. Keep it natural.")
        prompt_parts.append("\nGenerate an engaging, authentic YouTube script that sounds natural and conversational.")
        prompt_parts.append("\nCRITICAL: Make sure to complete the entire script. Do not stop mid-sentence or leave sections incomplete. The script must be complete from beginning to end.")
        prompt_parts.append("\nCOMPLETION REQUIREMENTS:\n- If the topic implies a list (e.g., \"Top 5 laptops\"), include exactly that many fully detailed items with consistent headings and balanced detail per item.\n- If you run out of room, compress wording rather than dropping items.\n- Ensure the script ends with a clear outro/CTA and a complete final sentence.")
        
        return "\n".join(prompt_parts)

    def _extract_text_from_response(self, response) -> Optional[str]:
        """Safely extract text from a Gemini response without triggering quick-accessor errors."""
        # Try quick accessor
        try:
            if getattr(response, 'text', None):
                return response.text
        except Exception:
            pass
        # Try candidates and parts
        try:
            if getattr(response, 'candidates', None):
                for cand in response.candidates:
                    content = getattr(cand, 'content', None)
                    if content and getattr(content, 'parts', None):
                        # Concatenate all text parts if available
                        parts_text = []
                        for p in content.parts:
                            t = getattr(p, 'text', None)
                            if t:
                                parts_text.append(t)
                        if parts_text:
                            return "\n".join(parts_text)
        except Exception:
            pass
        # Fallback to string
        try:
            s = str(response)
            return s if s else None
        except Exception:
            return None

    def _attempt_continuation(self, current_text: str, hard_word_cap: int, generation_config: Dict) -> str:
        """If the model stopped early, request continuation until cap/outro reached."""
        try:
            remaining_words = max(0, hard_word_cap - len(current_text.split()))
            if remaining_words < 50:
                return current_text
            tail = " ".join(current_text.split()[-80:])
            continuation_prompt = (
                f"Continue the script from where it stopped. Do not repeat any sentences. "
                f"Finish the remaining sections and end with a proper outro. "
                f"You have approximately {remaining_words} words remaining (total cap {hard_word_cap}). "
                f"Here are the last lines to continue from:\n" + tail
            )
            more = self.model.generate_content(continuation_prompt, generation_config=generation_config)
            if more and getattr(more, 'text', None):
                combined = current_text.rstrip() + "\n\n" + more.text.strip()
                return self._truncate_to_words_sentence_aware(combined, hard_word_cap)
        except Exception:
            return current_text
        return current_text

    def _attempt_guided_continuation(self, current_text: str, hard_word_cap: int, generation_config: Dict, guidance: str) -> str:
        """Continuation with guidance for remaining list items."""
        try:
            remaining_words = max(0, hard_word_cap - len(current_text.split()))
            if remaining_words < 50:
                return current_text
            tail = " ".join(current_text.split()[-80:])
            continuation_prompt = (
                guidance +
                f"You have approximately {remaining_words} words remaining (total cap {hard_word_cap}). "
                f"Here are the last lines to continue from:\n" + tail
            )
            more = self.model.generate_content(continuation_prompt, generation_config=generation_config)
            if more and getattr(more, 'text', None):
                combined = current_text.rstrip() + "\n\n" + more.text.strip()
                return self._truncate_to_words_sentence_aware(combined, hard_word_cap)
        except Exception:
            return current_text
        return current_text

    def _extract_expected_item_count(self, topic: str, additional_context: Optional[str]) -> Optional[int]:
        """Extract expected item count from topic/context (e.g., 'Top 5', '5 laptops')."""
        import re
        text = " ".join([t for t in [topic, additional_context] if t])
        patterns = [r"top\s+(\d+)", r"\b(\d+)\s*(?:items?|laptops?|phones?|mobiles?|tips?|points?)\b"]
        candidates = []
        for pat in patterns:
            for m in re.findall(pat, text, flags=re.IGNORECASE):
                try:
                    candidates.append(int(m))
                except Exception:
                    pass
        return max(candidates) if candidates else None

    def _count_list_items(self, text: str) -> int:
        """Heuristic count of enumerated items in the current script."""
        import re
        lines = [ln.strip() for ln in text.split('\n')]
        count = 0
        for ln in lines:
            if re.match(r"^(?:\d+[\).]|[-*]\s)\s*", ln):
                count += 1
            elif re.match(r"^\*\*\s*\w+\s*\d+\s*\*\*", ln):
                count += 1
            elif re.match(r"^(?:laptop|phone|item)\s*\d+[:\-]", ln, flags=re.IGNORECASE):
                count += 1
        return count
    
    def _clean_response_text(self, text: str) -> str:
        """Clean and fix encoding issues in the response text"""
        import re
        
        # First, try to decode and re-encode to fix encoding issues
        try:
            # Remove any replacement characters and fix common encoding issues
            cleaned_text = text.encode('utf-8', errors='ignore').decode('utf-8')
        except:
            cleaned_text = text
        
        # Remove problematic Unicode characters that cause display issues
        cleaned_text = re.sub(r'[\u200B-\u200D\uFEFF]', '', cleaned_text)  # Remove zero-width characters
        # IMPORTANT: Do NOT collapse spaces between Devanagari characters; that destroys word boundaries.
        
        # Remove any remaining replacement characters
        cleaned_text = re.sub(r'\uFFFD+', '', cleaned_text)
        
        # Clean up excessive whitespace
        cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)  # Remove excessive line breaks
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)  # Normalize spaces
        
        # Ensure proper line breaks
        cleaned_text = cleaned_text.replace('\r\n', '\n').replace('\r', '\n')
        
        return cleaned_text
    
    def _get_language_mix_description(self, creator_data: Dict) -> str:
        """Get language mix description for creator"""
        pref = creator_data.get('language_preferences', {})
        
        if pref.get('hindi_dominant', 0) > pref.get('english_dominant', 0):
            return "Hindi-dominant Hinglish (more Hindi expressions, Hindi grammatical structure)"
        elif pref.get('english_dominant', 0) > pref.get('hindi_dominant', 0):
            return "English-dominant Hinglish (more English words, English grammatical structure)"
        else:
            return "Balanced Hinglish (equal mix of Hindi and English)"
    
    def _get_tone_description(self, creator_data: Dict) -> str:
        """Get tone description for creator"""
        tone_profile = creator_data.get('tone_profile', {})
        
        parts = []
        if tone_profile.get('enthusiasm', 0) > 7:
            parts.append("Highly enthusiastic")
        if tone_profile.get('technical_depth', 0) > 7:
            parts.append("Technical and detailed")
        if tone_profile.get('friendliness', 0) > 7:
            parts.append("Friendly and approachable")
        
        return ", ".join(parts) if parts else "Balanced conversational tone"
    
    def _get_tone_guidelines(self, tone: str) -> str:
        """Get specific guidelines for requested tone"""
        tone_guidelines = {
            'friendly_and_informative': """
- Use conversational tone
- Include friendly greetings and transitions
- Make technical concepts accessible
- Ask rhetorical questions to engage audience
""",
            'enthusiastic_and_energetic': """
- High energy language
- Use enthusiastic expressions frequently
- Create excitement about the topic
- Include dramatic emphasis on key points
""",
            'professional_and_formal': """
- More structured and formal language
- Technical accuracy is paramount
- Measured pace and tone
- Professional vocabulary choices
""",
            'casual_and_conversational': """
- Relaxed, everyday language
- Use contractions and casual expressions
- As if talking to a friend
- Include personal opinions and reactions
""",
            'dramatic_and_engaging': """
- Build suspense and excitement
- Use dramatic words and expressions
- Create a story-like narrative
- Make the audience anticipate what comes next
""",
            'technical_and_detailed': """
- Focus on specifications and technical details
- Use precise technical vocabulary
- Include comparisons and benchmarks
- Detailed explanations of features
""",
            'humorous_and_entertaining': """
- Include humor and jokes
- Use wit and clever observations
- Make the content entertaining
- Balance information with entertainment
"""
        }
        
        return tone_guidelines.get(tone, tone_guidelines['friendly_and_informative'])
    
    def _get_content_type_guidelines(self, content_type: str) -> str:
        """Get guidelines for specific content types"""
        content_guidelines = {
            'review': """
- Structure: Introduction -> Key Features -> Pros/Cons -> Performance -> Price Conclusion
- Include comparisons with similar products
- Cover practical usage scenarios
- Provide clear recommendations
""",
            'comparison': """
- Structure: Introduction -> Feature-by-feature comparison -> Performance comparison -> Value analysis -> Winner
- Create fair comparisons
- Highlight key differences
- Provide clear winner with reasoning
""",
            'guide': """
- Structure: Problem introduction -> Step-by-step solution -> Tips and tricks -> Summary
- Clear instructions with actionable steps
- Cover different scenarios
- Include troubleshooting tips
""",
            'news': """
- Structure: Breaking news -> Context and background -> Analysis -> Future implications
- Start with the most important information
- Provide context for viewers
- Analyze implications and next steps
""",
            'general': """
- Structure: Introduction -> Main content points -> Summary -> Conclusion
- Balanced mix of information and entertainment
- Engaging throughout the duration
- Clear main message or takeaway
"""
        }
        
        return content_guidelines.get(content_type, content_guidelines['general'])
    
    def _post_process_script(self, raw_script: str, target_minutes: int, hard_word_cap: int) -> Dict[str, any]:
        """Post-process the generated script for formatting, enforce hard limits, and ensure a clean ending"""
        
        # Clean and format the script
        lines = raw_script.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        
        formatted_script = []
        current_section = "Introduction"
        
        # Parse and reformat sections
        for line in cleaned_lines:
            if line.lower().startswith(('hook', 'intro', 'main', 'conclusion', 'outro', 'cta')):
                current_section = line.strip()
                formatted_script.append(f"\n[{current_section.upper()}]\n")
            else:
                formatted_script.append(line)
        
        script_text = "\n".join(formatted_script)
        
        # Enforce word cap with sentence-aware truncation
        script_text = self._truncate_to_words_sentence_aware(script_text, hard_word_cap)
        
        # Ensure the script ends at a sentence boundary; do not force a canned outro
        script_text = self._ensure_sentence_boundary(script_text)
        
        # Estimate word count and speaking time
        word_count = len(script_text.split())
        estimated_minutes = word_count / 150  # Average 150 words per minute
        
        # Adjust if too long/short
        if estimated_minutes > target_minutes * 1.2:
            estimated_minutes = round(word_count / 150, 1)
        
        # Create timing suggestions
        timing_suggestions = self._create_timing_suggestions(target_minutes)
        
        return {
            'script': script_text,
            'word_count': word_count,
            'speaking_time': estimated_minutes,
            'timing_suggestions': timing_suggestions,
            'pattern_markers': self._extract_applied_patterns(script_text)
        }

    def _truncate_to_words_sentence_aware(self, text: str, max_words: int) -> str:
        """Trim text to max_words, preferring to cut at sentence boundaries.
        Supports English (. ! ?) and Hindi danda (।) plus pipes often used as separators.
        """
        words = text.split()
        if len(words) <= max_words:
            return text
        # Build provisional trimmed text
        provisional = " ".join(words[:max_words])
        # Find last sentence boundary before cutoff
        import re
        # Include common sentence-ending punctuation
        boundary_regex = re.compile(r"[\.\!\?\|\u0964]\s")  # \u0964 is '।'
        last_boundary_idx = -1
        for match in boundary_regex.finditer(provisional):
            last_boundary_idx = match.end()
        if last_boundary_idx != -1:
            trimmed = provisional[:last_boundary_idx].strip()
        else:
            trimmed = provisional.strip()
        return trimmed

    def _ensure_sentence_boundary(self, text: str) -> str:
        """Ensure the script ends at a clean sentence boundary without injecting canned text."""
        import re
        cleaned = text.rstrip()
        # If not ending with sentence punctuation, add a period
        if not re.search(r"[\.\!\?\u0964]$", cleaned):
            cleaned = cleaned + "."
        return cleaned
    
    def _create_timing_suggestions(self, target_minutes: int) -> Dict[str, str]:
        """Create timing suggestions for video production"""
        total_seconds = target_minutes * 60
        
        return {
            'hook_duration': '10-15 seconds',
            'intro_duration': '15-20 seconds', 
            'main_content_start': f'{25} seconds',
            'cta_timing': f'{total_seconds - 30} seconds',
            'outro_timing': f'{total_seconds - 15} seconds',
            'total_target': f'{target_minutes} minutes'
        }
    
    def _extract_applied_patterns(self, script: str) -> Dict[str, List[str]]:
        """Identify which creator patterns were applied in the script"""
        detected_patterns = {
            'hinglish_expressions': [],
            'engagement_phrases': [],
            'technical_terms': [],
            'transition_words': []
        }
        
        script_lower = script.lower()
        
        # Check for common Hinglish expressions
        hinglish_exprs = ['दोस्तों', 'भाई', 'यार', 'सुनिए', 'देखिए', 'तो यहाँ पर']
        for expr in hinglish_exprs:
            if expr in script_lower:
                detected_patterns['hinglish_expressions'].append(expr)
        
        # Check for engagement phrases
        engagement_phrases = ['subscribe', 'like', 'notification', 'bell', 'comment', 'share']
        for phrase in engagement_phrases:
            if phrase in script_lower:
                detected_patterns['engagement_phrases'].append(phrase)
        
        return detected_patterns
    
    def save_training_context(self, filepath: str):
        """Save training context to file for future use"""
        context_save_data = {
            'creator_styles': self.creator_styles,
            'training_context': self.training_context,
            'generation_config': self.generation_config
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(context_save_data, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] Training context saved to {filepath}")
    
    def load_training_context(self, filepath: str):
        """Load previously saved training context"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                context_data = json.load(f)
            
            self.creator_styles = context_data.get('creator_styles', {})
            self.training_context = context_data.get('training_context', {})
            
            print(f"[OK] Training context loaded from {filepath}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error loading training context: {e}")
            return False

