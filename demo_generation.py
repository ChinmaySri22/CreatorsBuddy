#!/usr/bin/env python3
"""
Demo Script for YouTube Script Generator
Shows how to use the generator programmatically without the web UI
"""

from config import Config
from transcript_processor import TranscriptProcessor
from script_generator import ScriptGenerator
from script_validator import ScriptValidator

def demo_script_generation():
    """Demonstrate script generation capabilities"""
    
    print("🎬 YouTube Script Generator - Demo Mode")
    print("=" * 50)
    
    try:
        # Step 1: Load and analyze transcripts
        print("📂 Loading transcript data...")
        processor = TranscriptProcessor(Config.DATA_DIR)
        transcripts = processor.load_all_transcripts()
        
        if not transcripts:
            print("❌ No transcripts found! Please ensure your data is in Data/processed/")
            return
        
        print(f"✅ Loaded {len(transcripts)} transcripts")
        
        # Show creator analysis
        creator_summary = processor.get_creator_summary()
        print(f"✅ Analyzed {len(creator_summary)} creators:")
        for creator, summary in creator_summary.items():
            print(f"   - {creator}: {summary['video_count']} videos, "
                  f"{summary['language_mix']['hindi_ratio']:.1%} Hindi")
        
        # Step 2: Train script generator
        print("\n🧠 Training script generator...")
        generator = ScriptGenerator()
        training_summary = generator.train_on_transcripts(transcripts)
        print(f"✅ Training completed: {training_summary['creators_analyzed']} creators analyzed")
        
        # Step 3: Generate some sample scripts
        print("\n📝 Generating sample scripts...")
        
        # Example 1: Tech review
        print("\n🔬 Example 1: Tech Review")
        print("-" * 30)
        
        result1 = generator.generate_script(
            topic="Samsung Galaxy S24 Ultra Camera Review",
            length_minutes=8,
            tone="enthusiastic_and_energetic", 
            target_audience="tech_enthusiasts",
            content_type="review",
            additional_context="Focus on night photography and AI features"
        )
        
        if result1['success']:
            print(f"✅ Generated: {result1['metadata']['estimated_word_count']} words, "
                  f"{result1['metadata']['generation_time_seconds']}s")
            print("\n📄 Preview:")
            preview1 = result1['script'][:400] + "..." if len(result1['script']) > 400 else result1['script']
            print(preview1)
            
            # Validate the script
            validator = ScriptValidator()
            validation = validator.validate_script(
                result1['script'],
                result1['metadata']['length_minutes'],
                result1['metadata']['tone_used'],
                result1['metadata']['target_audience'],
                "review"
            )
            
            print(f"\n✅ Validation Score: {validation.overall_score:.2f}/1.0")
            if validation.issues:
                print("⚠️  Issues:", "; ".join(validation.issues[:2]))
            if validation.suggestions:
                print("💡 Suggestions:", "; ".join(validation.suggestions[:2]))
        
        else:
            print(f"❌ Generation failed: {result1.get('error')}")
        
        # Example 2: Comparison video
        print("\n⚔️ Example 2: Comparison Video")
        print("-" * 30)
        
        result2 = generator.generate_script(
            topic="iPhone 15 Pro vs OnePlus 12 - Which is Better?",
            length_minutes=10,
            tone="technical_and_detailed",
            target_audience="tech_enthusiasts", 
            content_type="comparison",
            additional_context="Compare performance, features, and value for money"
        )
        
        if result2['success']:
            print(f"✅ Generated: {result2['metadata']['estimated_word_count']} words, "
                  f"{result2['metadata']['generation_time_seconds']}s")
            print("\n📄 Preview:")
            preview2 = result2['script'][:400] + "..." if len(result2['script']) > 400 else result2['script']
            print(preview2)
        else:
            print(f"❌ Generation failed: {result2.get('error')}")
        
        # Example 3: Tutorial
        print("\n🔧 Example 3: Tutorial")
        print("-" * 30)
        
        result3 = generator.generate_script(
            topic="How to Choose Perfect Gaming Phone in 2024",
            length_minutes=6,
            tone="friendly_and_informative",
            target_audience="gamers",
            content_type="tutorial",
            additional_context="Step-by-step guide with key specifications to look for"
        )
        
        if result3['success']:
            print(f"✅ Generated: {result3['metadata']['estimated_word_count']} words, "
                  f"{result3['metadata']['generation_time_seconds']}s")
            print("\n📄 Preview:")
            preview3 = result3['script'][:400] + "..." if len(result3['script']) > 400 else result3['script']
            print(preview3)
        else:
            print(f"❌ Generation failed: {result3.get('error')}")
        
        print("\n" + "=" * 50)
        print("🎉 Demo completed successfully!")
        print("💡 Use the web UI for interactive script generation:")
        print("   python run_app.py")
        print("=" * 50)
        
    except Exception as e:
        print(f"💥 Demo failed: {e}")
        print("Please check your configuration and data setup")

def demo_custom_generation():
    """Demo custom parameter generation"""
    
    print("\n🎨 Custom Generation Demo")
    print("=" * 30)
    
    try:
        # Initialize components
        processor = TranscriptProcessor(Config.DATA_DIR)
        transcripts = processor.load_all_transcripts()
        generator = ScriptGenerator()
        generator.train_on_transcripts(transcripts)
        
        # Custom scenarios
        scenarios = [
            {
                'title': 'Budget Smartphone Review',
                'params': {
                    'topic': 'Best Phone Under 15000',
                    'length_minutes': 7,
                    'tone': 'casual_and_conversational',
                    'target_audience': 'beginners',
                    'content_type': 'review',
                    'additional_context': 'Focus on value for money and daily usage'
                }
            },
            {
                'title': 'Premium Phone Launch',
                'params': {
                    'topic': 'Nothing Phone 2a Launch Unboxing',
                    'length_minutes': 12,
                    'tone': 'dramatic_and_engaging',
                    'target_audience': 'tech_enthusiasts',
                    'content_type': 'unboxing',
                    'additional_context': 'Exciting unboxing with first impressions and specs reveal'
                }
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🎬 Scenario {i}: {scenario['title']}")
            print("-" * 40)
            
            result = generator.generate_script(**scenario['params'])
            
            if result['success']:
                print(f"✅ Success! Generated {result['metadata']['estimated_word_count']} words")
                print(f"🎭 Tone: {result['metadata']['tone_used']}")
                print(f"👥 Audience: {result['metadata']['target_audience']}")
                
                # Show first paragraph
                lines = result['script'].split('\n')
                first_content = [l for l in lines if l.strip() and not l.startswith('[')][:3]
                if first_content:
                    print("\n📝 Opening lines:")
                    for line in first_content:
                        print(f"   {line}")
                        
    except Exception as e:
        print(f"❌ Custom demo failed: {e}")

if __name__ == "__main__":
    try:
        demo_script_generation()
        
        # Ask if user wants custom demo
        response = input("\n🎨 Run custom parameter demo? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            demo_custom_generation()
            
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo error: {e}")
        print("Make sure your environment is properly configured")

