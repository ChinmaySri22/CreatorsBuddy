#!/usr/bin/env python3
"""
Test Script for YouTube Script Generator
Quick test to verify the system works with your data
"""

import os
import json
from pathlib import Path

# Import our modules
from config import Config
from transcript_processor import TranscriptProcessor
from script_generator import ScriptGenerator

def test_environment():
    """Test if environment is set up correctly"""
    print("🔍 Testing environment...")
    
    # Check API key
    if not Config.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not configured!")
        return False
    print("✅ GEMINI_API_KEY configured")
    
    # Check data directory
    if not Path(Config.DATA_DIR).exists():
        print("❌ Data directory not found!")
        return False
    print("✅ Data directory exists")
    
    return True

def test_transcript_loading():
    """Test transcript loading and processing"""
    print("\n📂 Testing transcript loading...")
    
    try:
        processor = TranscriptProcessor(Config.DATA_DIR)
        transcripts = processor.load_all_transcripts()
        
        if not transcripts:
            print("❌ No transcripts loaded!")
            return False
        
        print(f"✅ Loaded {len(transcripts)} transcripts")
        
        # Show sample creator
        creator_summary = processor.get_creator_summary()
        if creator_summary:
            creator_name = list(creator_summary.keys())[0]
            summary = creator_summary[creator_name]
            print(f"✅ Sample creator '{creator_name}':")
            print(f"   - Videos: {summary['video_count']}")
            print(f"   - Language mix: {summary['language_mix']['hindi_ratio']:.1%} Hindi")
        
        return transcripts
        
    except Exception as e:
        print(f"❌ Error loading transcripts: {e}")
        return None

def test_script_generation(test_transcripts):
    """Test script generation capability"""
    print("\n🚀 Testing script generation...")
    
    try:
        generator = ScriptGenerator()
        
        # Test training first
        print("🧠 Training generator...")
        training_summary = generator.train_on_transcripts(test_transcripts)
        print(f"✅ Training completed: {training_summary}")
        
        # Test generation
        print("📝 Generating sample script...")
        result = generator.generate_script(
            topic="iPhone 15 Review",
            length_minutes=5,
            tone="friendly_and_informative",
            target_audience="tech_enthusiasts",
            content_type="review",
            additional_context="Focus on camera and battery performance"
        )
        
        if result['success']:
            script = result['script']
            print(f"✅ Script generated successfully!")
            print(f"   - Length: {len(script)} characters")
            print(f"   - Word count: {result['metadata']['estimated_word_count']}")
            print(f"   - Generation time: {result['metadata']['generation_time_seconds']}s")
            
            # Show preview
            preview = script[:300] + "..." if len(script) > 300 else script
            print(f"\n📄 Script Preview:")
            print("-" * 40)
            print(preview)
            print("-" * 40)
            
            return True
        else:
            print(f"❌ Script generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during generation test: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("=" * 50)
    print("🧪 YouTube Script Generator - Test Suite")
    print("=" * 50)
    
    # Test 1: Environment
    if not test_environment():
        print("\n❌ Environment tests failed!")
        return False
    
    # Test 2: Transcript loading
    transcripts = test_transcript_loading()
    if not transcripts:
        print("\n❌ Transcript loading tests failed!")
        return False
    
    # Test 3: Script generation
    if not test_script_generation(transcripts):
        print("\n❌ Script generation tests failed!")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed!")
    print("🚀 Your YouTube Script Generator is ready to use!")
    print("💡 Run 'python run_app.py' to start the web interface")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print("Please check your configuration and try again")

