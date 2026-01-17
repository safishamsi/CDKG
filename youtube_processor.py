"""
YouTube Video Processor - Download, transcribe, and add YouTube videos to the knowledge graph

This module:
1. Accepts YouTube URLs
2. Downloads video metadata and transcripts
3. Processes transcripts into the pipeline
4. Adds to Neo4j and vector database
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import yt_dlp
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

from config import config
from ner_intent_processor import get_processor

# Try to import Whisper for audio transcription
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️  Whisper not available. Install with: pip install openai-whisper")


class YouTubeVideoProcessor:
    """Process YouTube videos and add them to the knowledge graph"""
    
    def __init__(self):
        """Initialize processor"""
        self.config = config
        self.driver = None
        self.embedding_model = None
        
        # Create directories
        self.downloads_dir = Path("youtube_downloads")
        self.downloads_dir.mkdir(exist_ok=True)
        
        self.transcripts_dir = Path("youtube_transcripts")
        self.transcripts_dir.mkdir(exist_ok=True)
        
        self.audio_dir = Path("youtube_audio")
        self.audio_dir.mkdir(exist_ok=True)
        
        # Initialize Whisper model (lazy loading)
        self.whisper_model = None
        
        # Initialize NER/Intent processor
        self.ner_processor = None
    
    def connect_neo4j(self):
        """Connect to Neo4j"""
        if not self.driver:
            self.driver = GraphDatabase.driver(
                self.config.neo4j.uri,
                auth=(self.config.neo4j.user, self.config.neo4j.password)
            )
            self.driver.verify_connectivity()
    
    def load_embedding_model(self):
        """Load sentence transformer model"""
        if not self.embedding_model:
            self.embedding_model = SentenceTransformer(
                self.config.embedding.model_name,
                device=self.config.embedding.device
            )
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]+)',
            r'youtube\.com\/embed\/([^&\n?]+)',
            r'youtube\.com\/v\/([^&\n?]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def download_video_info(self, url: str) -> Dict:
        """Download video metadata and transcript using yt-dlp"""
        print(f"\n📥 Downloading video info from: {url}")
        
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {url}")
        
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'subtitlesformat': 'vtt',
            'outtmpl': str(self.downloads_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Download subtitles
                ydl.download([url])
                
                video_info = {
                    'video_id': video_id,
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'uploader': info.get('uploader', ''),
                    'upload_date': info.get('upload_date', ''),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'tags': info.get('tags', []),
                    'categories': info.get('categories', []),
                    'url': url,
                    'thumbnail': info.get('thumbnail', ''),
                }
                
                print(f"   ✅ Video: {video_info['title']}")
                print(f"   ✅ Uploader: {video_info['uploader']}")
                print(f"   ✅ Duration: {video_info['duration']}s")
                
                return video_info
        
        except Exception as e:
            print(f"   ❌ Error downloading video info: {e}")
            raise
    
    def extract_transcript_from_vtt(self, vtt_file: Path) -> Tuple[str, List[Dict]]:
        """Extract text and timestamps from VTT subtitle file"""
        if not vtt_file.exists():
            return "", []
        
        with open(vtt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # VTT format: timestamp --> timestamp followed by text
        pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3})\s-->\s(\d{2}:\d{2}:\d{2}\.\d{3})\n(.*?)(?=\n\n|\n\d{2}:|$)'
        
        matches = re.finditer(pattern, content, re.DOTALL)
        
        text_parts = []
        segments = []
        
        for match in matches:
            start_time = match.group(1)
            end_time = match.group(2)
            text = match.group(3)
            
            # Clean up text
            text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
            text = re.sub(r'\n+', ' ', text)
            text = text.strip()
            
            if text:
                text_parts.append(text)
                
                # Convert to seconds
                start_seconds = self.time_to_seconds(start_time)
                end_seconds = self.time_to_seconds(end_time)
                
                segments.append({
                    'start': start_time,
                    'end': end_time,
                    'start_seconds': start_seconds,
                    'end_seconds': end_seconds,
                    'duration_seconds': end_seconds - start_seconds,
                    'text': text
                })
        
        full_text = ' '.join(text_parts)
        return full_text, segments
    
    def time_to_seconds(self, time_str: str) -> float:
        """Convert time string (HH:MM:SS.mmm) to seconds"""
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
    
    def find_subtitle_file(self, video_id: str) -> Optional[Path]:
        """Find downloaded subtitle file"""
        # Look for .en.vtt or .vtt files
        for pattern in ['*.en.vtt', '*.vtt']:
            files = list(self.downloads_dir.glob(f"{video_id}.{pattern}"))
            if files:
                return files[0]
        
        return None
    
    def download_audio(self, url: str, video_id: str) -> Optional[Path]:
        """Download audio from YouTube video"""
        print(f"\n🎵 Downloading audio...")
        
        # yt-dlp will add .mp3 extension via postprocessor
        audio_file = self.audio_dir / f"{video_id}.mp3"
        
        # Skip if already downloaded
        if audio_file.exists():
            print(f"   ✅ Audio already exists: {audio_file}")
            return audio_file
        
        # Use base filename without extension for outtmpl
        audio_base = self.audio_dir / video_id
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(audio_base),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Check for the file (might be .mp3 or other format)
            if audio_file.exists():
                print(f"   ✅ Audio downloaded: {audio_file}")
                return audio_file
            else:
                # Try to find any audio file with the video_id
                audio_files = list(self.audio_dir.glob(f"{video_id}.*"))
                if audio_files:
                    audio_file = audio_files[0]
                    print(f"   ✅ Audio downloaded: {audio_file}")
                    return audio_file
                else:
                    print(f"   ❌ Audio file not found after download")
                    return None
        except Exception as e:
            print(f"   ❌ Error downloading audio: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def transcribe_audio(self, audio_file: Path) -> Tuple[str, List[Dict]]:
        """Transcribe audio file using Whisper"""
        if not WHISPER_AVAILABLE:
            raise ImportError("Whisper not available. Install with: pip install openai-whisper")
        
        print(f"\n🎤 Transcribing audio with Whisper...")
        
        # Load Whisper model (lazy loading)
        if not self.whisper_model:
            print("   Loading Whisper model (this may take a moment on first use)...")
            self.whisper_model = whisper.load_model("base")  # Use 'base' for speed, 'medium' or 'large' for accuracy
        
        # Transcribe
        print(f"   Transcribing {audio_file.name}...")
        result = self.whisper_model.transcribe(str(audio_file), language="en")
        
        # Extract text and segments
        full_text = result["text"]
        segments = []
        
        for segment in result.get("segments", []):
            segments.append({
                'start': self.seconds_to_time(segment['start']),
                'end': self.seconds_to_time(segment['end']),
                'start_seconds': segment['start'],
                'end_seconds': segment['end'],
                'duration_seconds': segment['end'] - segment['start'],
                'text': segment['text'].strip()
            })
        
        print(f"   ✅ Transcribed {len(full_text)} characters")
        print(f"   ✅ Found {len(segments)} segments")
        
        return full_text, segments
    
    def seconds_to_time(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS.mmm format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{int(secs):02d}.{int((secs % 1) * 1000):03d}"
    
    def create_talk_node(self, video_info: Dict, transcript: str, segments: List[Dict], 
                         ner_data: Optional[Dict] = None) -> bool:
        """Create or update Talk node in Neo4j with NER, context, and intent"""
        print(f"\n💾 Storing in Neo4j...")
        
        self.connect_neo4j()
        
        # Format tags as array (stored as property on Talk, not as separate nodes)
        tags = [tag.strip().lower() for tag in video_info.get('tags', [])[:10] if tag and tag.strip()]
        
        # Store segments as JSON
        segments_json = json.dumps(segments) if segments else None
        
        # Format upload date
        upload_date = video_info.get('upload_date', '')
        if upload_date and len(upload_date) == 8:
            # Convert YYYYMMDD to YYYY-MM-DD
            upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
        
        # Prepare NER data
        entities_json = json.dumps(ner_data.get('entities', {})) if ner_data else None
        concepts_json = json.dumps(ner_data.get('key_concepts', [])) if ner_data else None
        intent_json = json.dumps(ner_data.get('intent', {})) if ner_data else None
        context_json = json.dumps(ner_data.get('context', {})) if ner_data else None
        
        with self.driver.session() as session:
            # Create or merge Talk node with tags as array property (not separate nodes)
            result = session.run("""
                MERGE (t:Talk {title: $title})
                SET t.description = $description,
                    t.category = $category,
                    t.url = $url,
                    t.type = 'YouTube Video',
                    t.transcript = $transcript,
                    t.transcript_length = $length,
                    t.transcript_segments = $segments,
                    t.transcript_segment_count = $segment_count,
                    t.youtube_id = $video_id,
                    t.duration = $duration,
                    t.view_count = $view_count,
                    t.like_count = $like_count,
                    t.upload_date = $upload_date,
                    t.thumbnail = $thumbnail,
                    t.tags = $tags,
                    t.entities = $entities,
                    t.key_concepts = $concepts,
                    t.intent = $intent,
                    t.context = $context,
                    t.added_date = datetime()
                RETURN t.title as title
            """,
                title=video_info['title'],
                description=video_info.get('description', '')[:1000],  # Limit description
                category=video_info['categories'][0] if video_info.get('categories') else 'YouTube',
                url=video_info['url'],
                transcript=transcript,
                length=len(transcript),
                segments=segments_json,
                segment_count=len(segments),
                video_id=video_info['video_id'],
                duration=video_info.get('duration', 0),
                view_count=video_info.get('view_count', 0),
                like_count=video_info.get('like_count', 0),
                upload_date=upload_date,
                thumbnail=video_info.get('thumbnail', ''),
                tags=tags,  # Store as array property
                entities=entities_json,
                concepts=concepts_json,
                intent=intent_json,
                context=context_json
            )
            
            if not result.single():
                print(f"   ❌ Failed to create Talk node")
                return False
            
            # Create Speaker node and relationship
            if video_info.get('uploader'):
                session.run("""
                    MERGE (s:Speaker {name: $speaker})
                    WITH s
                    MATCH (t:Talk {title: $title})
                    MERGE (s)-[:GIVES_TALK]->(t)
                """,
                    speaker=video_info['uploader'],
                    title=video_info['title']
                )
                print(f"   ✅ Linked speaker: {video_info['uploader']}")
            
            # Tags are now stored as property on Talk node (not separate nodes)
            if tags:
                print(f"   ✅ Added {len(tags)} tags as Talk property")
            
            # Create entity nodes from NER results
            if ner_data and ner_data.get('entities'):
                entity_count = 0
                for entity_type, entities in ner_data['entities'].items():
                    for entity in entities:
                        entity_text = entity['text']
                        # Create entity node based on type
                        if entity_type == 'PERSON':
                            session.run("""
                                MERGE (e:Speaker {name: $name})
                                WITH e
                                MATCH (t:Talk {title: $title})
                                MERGE (t)-[:MENTIONS]->(e)
                            """,
                                name=entity_text,
                                title=video_info['title']
                            )
                            entity_count += 1
                        elif entity_type == 'ORG':
                            session.run("""
                                MERGE (e:Organization {name: $name})
                                WITH e
                                MATCH (t:Talk {title: $title})
                                MERGE (t)-[:MENTIONS]->(e)
                            """,
                                name=entity_text,
                                title=video_info['title']
                            )
                            entity_count += 1
                        elif entity_type == 'PRODUCT':
                            session.run("""
                                MERGE (e:Product {name: $name})
                                WITH e
                                MATCH (t:Talk {title: $title})
                                MERGE (t)-[:MENTIONS]->(e)
                            """,
                                name=entity_text,
                                title=video_info['title']
                            )
                            entity_count += 1
                
                if entity_count > 0:
                    print(f"   ✅ Created {entity_count} entity nodes")
            
            # Create concept nodes from key concepts
            if ner_data and ner_data.get('key_concepts'):
                concept_count = 0
                for concept_info in ner_data['key_concepts'][:10]:  # Top 10 concepts
                    concept = concept_info['concept']
                    session.run("""
                        MERGE (c:Concept {name: $concept})
                        SET c.frequency = $frequency,
                            c.importance = $importance
                        WITH c
                        MATCH (t:Talk {title: $title})
                        MERGE (t)-[:DISCUSSES]->(c)
                    """,
                        concept=concept,
                        frequency=concept_info.get('frequency', 0),
                        importance=concept_info.get('importance', 0),
                        title=video_info['title']
                    )
                    concept_count += 1
                
                if concept_count > 0:
                    print(f"   ✅ Created {concept_count} concept nodes")
            
            # Create/link to YouTube Event
            session.run("""
                MERGE (e:Event {name: 'YouTube Videos'})
                SET e.description = 'Videos added from YouTube',
                    e.type = 'YouTube'
                WITH e
                MATCH (t:Talk {title: $title})
                MERGE (t)-[:IS_PART_OF]->(e)
            """,
                title=video_info['title']
            )
            
            print(f"   ✅ Talk node created: {video_info['title']}")
        
        return True
    
    def generate_and_store_embedding(self, video_info: Dict, transcript: str):
        """Generate embedding and update FAISS index"""
        print(f"\n🧠 Generating embedding...")
        
        self.load_embedding_model()
        
        # Create rich text representation
        text = f"Talk: {video_info['title']} by {video_info.get('uploader', 'Unknown')}. "
        text += f"Description: {video_info.get('description', '')[:500]}. "
        text += f"Transcript: {transcript[:1000]}"  # First 1000 chars of transcript
        
        # Generate embedding
        embedding = self.embedding_model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        
        # Save embedding
        embeddings_dir = config.paths.embeddings_dir
        
        # Load existing embeddings
        import numpy as np
        import faiss
        
        all_embeddings_file = embeddings_dir / "all_embeddings.npy"
        index_mapping_file = embeddings_dir / "index_mapping.json"
        faiss_index_file = embeddings_dir / "faiss_index.bin"
        
        # Load existing data
        all_embeddings = np.load(all_embeddings_file)
        with open(index_mapping_file, 'r') as f:
            index_mapping = json.load(f)
        
        index = faiss.read_index(str(faiss_index_file))
        
        # Add new embedding
        new_embedding = embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(new_embedding)
        
        index.add(new_embedding)
        
        # Update mapping
        new_index = len(index_mapping)
        index_mapping.append({
            'index': new_index,
            'node_type': 'Talk',
            'metadata': {
                'title': video_info['title'],
                'description': video_info.get('description', '')[:200],
                'speaker': video_info.get('uploader', ''),
                'tags': video_info.get('tags', [])[:5],
                'youtube_id': video_info['video_id']
            }
        })
        
        # Update embeddings array
        all_embeddings = np.vstack([all_embeddings, new_embedding])
        
        # Save updated data
        np.save(all_embeddings_file, all_embeddings)
        faiss.write_index(index, str(faiss_index_file))
        with open(index_mapping_file, 'w') as f:
            json.dump(index_mapping, f, indent=2)
        
        print(f"   ✅ Embedding added to vector store")
        print(f"   ✅ Total embeddings: {len(index_mapping)}")
    
    def process_youtube_url(self, url: str) -> bool:
        """
        Complete pipeline: Download, transcribe, and add YouTube video
        
        Args:
            url: YouTube video URL
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print("\n" + "=" * 70)
            print(f"🎬 PROCESSING YOUTUBE VIDEO")
            print("=" * 70)
            
            # Step 1: Download video info and subtitles
            video_info = self.download_video_info(url)
            
            # Step 2: Try to get transcript (subtitles first, then audio transcription)
            print(f"\n📝 Extracting transcript...")
            subtitle_file = self.find_subtitle_file(video_info['video_id'])
            
            transcript = ""
            segments = []
            transcript_source = None
            
            if subtitle_file:
                # Use subtitles if available
                print(f"   ✅ Found subtitles, extracting...")
                transcript, segments = self.extract_transcript_from_vtt(subtitle_file)
                transcript_source = "subtitles"
            elif WHISPER_AVAILABLE:
                # Fallback to audio transcription
                print(f"   ⚠️  No subtitles found, falling back to audio transcription...")
                audio_file = self.download_audio(url, video_info['video_id'])
                
                if audio_file:
                    transcript, segments = self.transcribe_audio(audio_file)
                    transcript_source = "audio_transcription"
                else:
                    print(f"   ❌ Failed to download audio for transcription")
                    return False
            else:
                print(f"   ❌ No subtitles found and Whisper not available")
                print(f"   💡 Install Whisper: pip install openai-whisper")
                return False
            
            if not transcript or len(transcript) < 100:
                print(f"   ❌ Transcript too short or empty")
                return False
            
            print(f"   ✅ Transcript source: {transcript_source}")
            
            print(f"   ✅ Extracted {len(transcript)} characters from {transcript_source}")
            print(f"   ✅ Found {len(segments)} segments")
            
            # Save transcript
            transcript_file = self.transcripts_dir / f"{video_info['video_id']}.txt"
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"   ✅ Saved to: {transcript_file}")
            
            # Step 3: Process with NER, context, and intent recognition
            ner_data = None
            try:
                if not self.ner_processor:
                    self.ner_processor = get_processor()
                
                ner_data = self.ner_processor.process_video(
                    title=video_info['title'],
                    description=video_info.get('description', ''),
                    transcript=transcript,
                    segments=segments
                )
            except Exception as e:
                print(f"   ⚠️  Error in NER/Intent processing: {e}")
                import traceback
                traceback.print_exc()
            
            # Step 4: Create Talk node in Neo4j (with NER data)
            success = self.create_talk_node(video_info, transcript, segments, ner_data)
            if not success:
                return False
            
            # Step 5: Generate and store embedding
            self.generate_and_store_embedding(video_info, transcript)
            
            print("\n" + "=" * 70)
            print("✅ YOUTUBE VIDEO PROCESSED SUCCESSFULLY!")
            print("=" * 70)
            print(f"\n📊 Summary:")
            print(f"   Title: {video_info['title']}")
            print(f"   Speaker: {video_info.get('uploader', 'Unknown')}")
            print(f"   Duration: {video_info['duration']}s")
            print(f"   Transcript: {len(transcript)} chars")
            print(f"   Segments: {len(segments)}")
            print(f"   Tags: {len(video_info.get('tags', []))}")
            print()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error processing video: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            if self.driver:
                self.driver.close()
    
    def process_multiple_urls(self, urls: List[str]) -> Dict[str, bool]:
        """
        Process multiple YouTube URLs
        
        Args:
            urls: List of YouTube URLs
            
        Returns:
            Dictionary mapping URLs to success status
        """
        results = {}
        
        print(f"\n🎬 Processing {len(urls)} YouTube videos...")
        
        for i, url in enumerate(urls, 1):
            print(f"\n{'='*70}")
            print(f"Video {i}/{len(urls)}")
            print(f"{'='*70}")
            
            success = self.process_youtube_url(url)
            results[url] = success
            
            if self.driver:
                self.driver.close()
                self.driver = None
        
        # Summary
        print(f"\n{'='*70}")
        print(f"📊 BATCH PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"   Total videos: {len(urls)}")
        print(f"   Successful: {sum(results.values())}")
        print(f"   Failed: {len(urls) - sum(results.values())}")
        print()
        
        return results


def main():
    """Test the YouTube processor"""
    processor = YouTubeVideoProcessor()
    
    # Example YouTube URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print("YouTube Video Processor - Test Mode")
    print("Enter a YouTube URL to process, or press Enter to exit:")
    
    url = input("> ").strip()
    
    if url:
        processor.process_youtube_url(url)
    else:
        print("No URL provided. Exiting.")


if __name__ == "__main__":
    main()
