"""
Test YouTube Video Integration

Quick test script to verify YouTube processing works
"""

from youtube_processor import YouTubeVideoProcessor


def test_youtube_integration():
    """Test the YouTube integration with a sample video"""
    
    print("=" * 70)
    print("🧪 TESTING YOUTUBE INTEGRATION")
    print("=" * 70)
    
    # Initialize processor
    print("\n1️⃣ Initializing processor...")
    processor = YouTubeVideoProcessor()
    print("   ✅ Processor initialized")
    
    # Test video (replace with your own)
    test_url = input("\n2️⃣ Enter YouTube URL to test (or press Enter for interactive mode): ").strip()
    
    if not test_url:
        print("\n📺 Interactive Mode")
        print("-" * 70)
        print("Enter YouTube URLs one at a time.")
        print("Press Enter without a URL to exit.")
        print()
        
        while True:
            url = input("YouTube URL: ").strip()
            if not url:
                print("\n✅ Exiting...")
                break
            
            try:
                success = processor.process_youtube_url(url)
                if success:
                    print("\n" + "=" * 70)
                    print("✅ SUCCESS! Video added to knowledge graph")
                    print("=" * 70)
                    print("\n💡 You can now query this video in your chatbot!")
                    print()
                else:
                    print("\n❌ Failed to process video")
                    print()
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print()
    else:
        # Process single URL
        print(f"\n3️⃣ Processing video: {test_url}")
        
        try:
            success = processor.process_youtube_url(test_url)
            
            if success:
                print("\n" + "=" * 70)
                print("✅ TEST PASSED!")
                print("=" * 70)
                print("\nThe video has been added to your knowledge graph.")
                print("You can now query it in your RAG chatbot!")
                print("\nTry asking:")
                print('  - "What did you learn from the video?"')
                print('  - "Summarize the video content"')
                print('  - "What topics were discussed?"')
                print()
            else:
                print("\n" + "=" * 70)
                print("❌ TEST FAILED")
                print("=" * 70)
                print("\nThe video could not be processed.")
                print("Common reasons:")
                print("  - Video has no subtitles/captions")
                print("  - Video is private or restricted")
                print("  - Network issues")
                print()
        
        except Exception as e:
            print("\n" + "=" * 70)
            print("❌ ERROR")
            print("=" * 70)
            print(f"\nError: {e}")
            print()


def test_batch_processing():
    """Test batch processing of multiple videos"""
    
    print("=" * 70)
    print("🧪 BATCH PROCESSING TEST")
    print("=" * 70)
    
    processor = YouTubeVideoProcessor()
    
    print("\nEnter YouTube URLs (one per line)")
    print("Press Enter twice when done")
    print()
    
    urls = []
    while True:
        url = input(f"URL {len(urls)+1}: ").strip()
        if not url:
            break
        urls.append(url)
    
    if not urls:
        print("No URLs provided")
        return
    
    print(f"\n📊 Processing {len(urls)} videos...")
    results = processor.process_multiple_urls(urls)
    
    # Summary
    successful = sum(results.values())
    print("\n" + "=" * 70)
    print("📊 BATCH RESULTS")
    print("=" * 70)
    print(f"Total: {len(urls)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(urls) - successful}")
    print()
    
    for url, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {url}")
    print()


def test_api_endpoints():
    """Test REST API endpoints"""
    import requests
    
    print("=" * 70)
    print("🧪 TESTING REST API")
    print("=" * 70)
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    print("\n1️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ API is running")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ API returned {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Could not connect to API: {e}")
        print(f"   💡 Make sure to run: python backend_api_youtube.py")
        return
    
    # Test adding video
    print("\n2️⃣ Testing video addition...")
    test_url = input("Enter YouTube URL to test: ").strip()
    
    if test_url:
        try:
            response = requests.post(
                f"{base_url}/api/youtube/add",
                json={"url": test_url}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Request accepted")
                print(f"   Job ID: {data.get('job_id')}")
                
                # Check status
                if data.get('job_id'):
                    import time
                    print("\n3️⃣ Checking status...")
                    
                    for i in range(30):  # Check for 60 seconds
                        time.sleep(2)
                        status_response = requests.get(
                            f"{base_url}/api/youtube/status/{data['job_id']}"
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            print(f"   Status: {status_data['status']} - {status_data['progress']}")
                            
                            if status_data['status'] in ['completed', 'failed']:
                                break
                    
                    if status_data['status'] == 'completed':
                        print("\n   ✅ Video successfully added!")
                    else:
                        print(f"\n   ❌ Processing failed: {status_data.get('error')}")
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("YouTube Integration Test Suite")
    print("=" * 70)
    print("\nChoose a test:")
    print("1. Single video test (direct)")
    print("2. Batch processing test")
    print("3. REST API test")
    print("4. Interactive mode")
    print()
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        test_youtube_integration()
    elif choice == "2":
        test_batch_processing()
    elif choice == "3":
        test_api_endpoints()
    elif choice == "4":
        processor = YouTubeVideoProcessor()
        print("\n📺 Interactive Mode - Enter URLs as they come!")
        while True:
            url = input("\nYouTube URL (or 'quit'): ").strip()
            if url.lower() in ['quit', 'exit', 'q']:
                break
            if url:
                processor.process_youtube_url(url)
    else:
        print("Invalid choice")
