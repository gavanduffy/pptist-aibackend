#!/usr/bin/env python3
"""
PPTist AI Backend API Test Script
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    return True

def test_ppt_outline():
    """Test PPT outline generation"""
    print("\n📝 Testing PPT outline generation...")
    
    data = {
        "model": "google/gemma-2-9b-it:free",
        "language": "English",
        "content": "Artificial Intelligence applications in education",
        "stream": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tools/aippt_outline",
            json=data,
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Outline generation request successful")
            print("📄 Generated outline content:")
            print("-" * 50)
            
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if chunk:
                    print(chunk, end='')
            print("\n" + "-" * 50)
        else:
            print(f"❌ Outline generation failed: {response.status_code}")
            print(f"Error message: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_ppt_content():
    """Test PPT content generation"""
    print("\n🎨 Testing PPT content generation...")
    
    # Use sample outline
    sample_outline = """# Artificial Intelligence in Education
## AI Education Overview
### Definition and Significance of AI Education
- Application of AI technology in education
- Improving teaching effectiveness and learning experience
- Promoting education modernization
### Development History of AI Education
- Early exploration phase
- Technology breakthrough period
- Large-scale application period
## Specific Application Scenarios
### Personalized Learning
- Intelligent recommendation of learning content
- Adaptive learning paths
- Learning effectiveness assessment"""
    
    data = {
        "model": "google/gemma-2-9b-it:free",
        "language": "English",
        "content": sample_outline,
        "stream": True
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/tools/aippt",
            json=data,
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Content generation request successful")
            print("🎯 Generated PPT pages:")
            print("-" * 50)
            
            page_count = 0
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if chunk.strip():
                    page_count += 1
                    print(f"Page {page_count}:")
                    try:
                        # Try to parse JSON for pretty output
                        page_data = json.loads(chunk.strip())
                        print(json.dumps(page_data, ensure_ascii=False, indent=2))
                    except json.JSONDecodeError:
                        print(chunk.strip())
                    print("-" * 30)
            print(f"Total of {page_count} pages generated")
        else:
            print(f"❌ Content generation failed: {response.status_code}")
            print(f"Error message: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def main():
    """Main test function"""
    print("🧪 PPTist AI Backend API Test")
    print("=" * 50)
    
    # Test server connection
    if not test_health():
        print("❌ Server not started or cannot connect")
        print("Please run: uv run main.py")
        return
    
    # Test outline generation
    test_ppt_outline()
    
    # Wait a bit before testing content generation
    time.sleep(2)
    
    # Test content generation
    test_ppt_content()
    
    print("\n🎉 Testing completed!")

if __name__ == "__main__":
    main()
