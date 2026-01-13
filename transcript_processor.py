"""
Transcript Processor - Extract and process transcript content

This module:
1. Extracts plain text from .srt and .txt files
2. Maps transcripts to Talk nodes using metadata CSV
3. Stores transcript content in Neo4j
"""

import re
import os
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import pandas as pd
from neo4j import GraphDatabase
from tqdm import tqdm

from config import config


def extract_text_from_srt(srt_content: str) -> tuple[str, list]:
    """
    Extract text and timestamps from .srt subtitle file
    
    Returns:
        tuple: (full_text, segments_list)
        - full_text: Plain text without timestamps (for embeddings)
        - segments_list: List of dicts with start, end, text, duration_seconds
    """
    # Pattern to match subtitle blocks: number, timestamp, text
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s-->\s(\d{2}:\d{2}:\d{2}[,\.]\d{3})\n(.*?)(?=\n\n|\n\d+\n|$)'
    
    matches = re.finditer(pattern, srt_content + '\n\n', re.DOTALL)
    
    text_parts = []
    segments = []
    
    for match in matches:
        seq_num = match.group(1)
        start_time = match.group(2).replace(',', '.')
        end_time = match.group(3).replace(',', '.')
        text = match.group(4)
        
        # Clean up text: remove HTML tags, normalize whitespace
        text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
        text = re.sub(r'\n+', ' ', text)  # Replace newlines with space
        text = text.strip()
        
        if text:
            text_parts.append(text)
            
            # Calculate duration in seconds
            start_seconds = time_to_seconds(start_time)
            end_seconds = time_to_seconds(end_time)
            duration = end_seconds - start_seconds
            
            segments.append({
                'sequence': int(seq_num),
                'start': start_time,
                'end': end_time,
                'start_seconds': start_seconds,
                'end_seconds': end_seconds,
                'duration_seconds': duration,
                'text': text
            })
    
    full_text = ' '.join(text_parts)
    return full_text, segments


def time_to_seconds(time_str: str) -> float:
    """Convert time string (HH:MM:SS.mmm) to seconds"""
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds_parts = parts[2].split('.')
    seconds = int(seconds_parts[0])
    milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
    return total_seconds


def extract_text_from_txt(txt_content: str) -> str:
    """Extract text from .txt file (already plain text)"""
    return txt_content.strip()


def load_transcript_metadata() -> Dict[str, Dict]:
    """Load transcript metadata CSV and create mapping"""
    metadata_file = Path(__file__).parent / "Transcripts" / "Connected Data Knowledge Graph Challenge - Transcript Metadata.csv"
    
    if not metadata_file.exists():
        print(f"⚠️  Metadata file not found: {metadata_file}")
        return {}
    
    df = pd.read_csv(metadata_file)
    
    # Create mapping: filename -> talk metadata
    mapping = {}
    for _, row in df.iterrows():
        file_path = row.get('File', '')
        # Handle NaN/None values
        if pd.isna(file_path) or not file_path or str(file_path).strip() == '':
            continue
        
        try:
            # Extract filename without extension
            filename = Path(str(file_path)).stem
            mapping[filename] = {
                'title': row.get('Title', ''),
                'speaker': row.get('Speaker', ''),
                'event': row.get('Event', ''),
                'file_path': str(file_path)
            }
        except Exception as e:
            print(f"   ⚠️  Error processing file path '{file_path}': {e}")
            continue
    
    return mapping


def find_transcript_files() -> list:
    """Find all transcript files (.srt and .txt)"""
    transcripts_dir = Path(__file__).parent / "Transcripts"
    
    transcript_files = []
    
    # Find .srt files
    for srt_file in transcripts_dir.rglob("*.srt"):
        transcript_files.append(srt_file)
    
    # Find .txt files
    for txt_file in transcripts_dir.rglob("*.txt"):
        transcript_files.append(txt_file)
    
    return transcript_files


def process_transcripts():
    """Main function to process all transcripts"""
    print("=" * 70)
    print("🚀 TRANSCRIPT PROCESSOR")
    print("=" * 70)
    
    # Load metadata mapping
    print("\n📋 Loading transcript metadata...")
    metadata_map = load_transcript_metadata()
    print(f"   ✅ Loaded metadata for {len(metadata_map)} transcripts\n")
    
    # Find transcript files
    print("📁 Finding transcript files...")
    transcript_files = find_transcript_files()
    print(f"   ✅ Found {len(transcript_files)} transcript files\n")
    
    # Connect to Neo4j
    print("🔌 Connecting to Neo4j...")
    driver = GraphDatabase.driver(
        config.neo4j.uri,
        auth=(config.neo4j.user, config.neo4j.password)
    )
    driver.verify_connectivity()
    print("   ✅ Connected\n")
    
    # Process each transcript
    print("=" * 70)
    print("Processing Transcripts")
    print("=" * 70 + "\n")
    
    processed = 0
    matched = 0
    not_found = []
    
    with driver.session() as session:
        for transcript_file in tqdm(transcript_files, desc="Processing"):
            try:
                # Read file
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract text and timestamps based on file type
                segments = None
                if transcript_file.suffix == '.srt':
                    text, segments = extract_text_from_srt(content)
                else:
                    text = extract_text_from_txt(content)
                    segments = []  # No timestamps for .txt files
                
                if not text or len(text.strip()) < 50:
                    continue  # Skip empty or very short transcripts
                
                # Find matching Talk node
                filename = transcript_file.stem
                metadata = metadata_map.get(filename)
                
                if not metadata:
                    # Try to find by partial filename match
                    for key, meta in metadata_map.items():
                        if key.lower() in filename.lower() or filename.lower() in key.lower():
                            metadata = meta
                            break
                
                if metadata and metadata.get('title'):
                    talk_title = metadata['title']
                    
                    # Store segments as JSON string
                    segments_json = json.dumps(segments) if segments else None
                    
                    # Update Talk node with transcript and timestamps
                    result = session.run("""
                        MATCH (t:Talk {title: $title})
                        SET t.transcript = $transcript,
                            t.transcript_length = $length,
                            t.transcript_file = $filename,
                            t.transcript_segments = $segments,
                            t.transcript_segment_count = $segment_count
                        RETURN t.title as title
                    """, 
                    title=talk_title,
                    transcript=text,
                    length=len(text),
                    filename=str(transcript_file.relative_to(Path(__file__).parent)),
                    segments=segments_json,
                    segment_count=len(segments) if segments else 0
                    )
                    
                    if result.single():
                        matched += 1
                    else:
                        not_found.append(f"{filename} -> {talk_title}")
                else:
                    not_found.append(f"{filename} (no metadata match)")
                
                processed += 1
                
            except Exception as e:
                print(f"\n   ⚠️  Error processing {transcript_file.name}: {e}")
                not_found.append(f"{transcript_file.name} (error: {str(e)[:50]})")
    
    # Statistics
    print("\n" + "=" * 70)
    print("📊 Processing Summary")
    print("=" * 70)
    print(f"   Total files processed: {processed}")
    print(f"   Successfully matched: {matched}")
    print(f"   Not matched: {len(not_found)}")
    
    if not_found:
        print(f"\n   ⚠️  Transcripts not matched:")
        for item in not_found[:10]:  # Show first 10
            print(f"      • {item}")
        if len(not_found) > 10:
            print(f"      ... and {len(not_found) - 10} more")
    
    # Check how many talks now have transcripts
    with driver.session() as session:
        result = session.run("""
            MATCH (t:Talk)
            WHERE t.transcript IS NOT NULL
            RETURN count(t) as count
        """)
        count = result.single()['count']
        print(f"\n   ✅ Talks with transcripts in Neo4j: {count}")
    
    driver.close()
    
    print("\n" + "=" * 70)
    print("✅ TRANSCRIPT PROCESSING COMPLETE!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    process_transcripts()

