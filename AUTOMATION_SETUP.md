# YouTube Automation Setup Guide

This guide explains how to set up automatic YouTube video ingestion for the Connected Data channel.

## Overview

The system automatically monitors the Connected Data YouTube channel and processes new videos with:
- **Automatic transcription** (subtitles or Whisper audio transcription)
- **Named Entity Recognition (NER)** using spaCy
- **Context extraction** from transcripts
- **Intent recognition** using LLM
- **Knowledge graph integration** with Neo4j

## Prerequisites

1. **YouTube Data API Key**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable "YouTube Data API v3"
   - Create credentials (API Key)
   - Add to `.env` file:
     ```
     YOUTUBE_API_KEY=your_api_key_here
     ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements_youtube.txt
   python -m spacy download en_core_web_sm
   ```

3. **Environment Variables**
   Make sure your `.env` file has:
   ```
   YOUTUBE_API_KEY=your_key
   ANTHROPIC_API_KEY=your_key
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

## Usage

### Option 1: API Endpoints (Recommended)

Start the backend API:
```bash
python backend_api_youtube.py
```

Then use the API endpoints:

**Start Monitoring:**
```bash
curl -X POST "http://localhost:8000/api/youtube/monitor/start?channel_username=@ConnectedData&check_interval_minutes=60"
```

**Check Status:**
```bash
curl "http://localhost:8000/api/youtube/monitor/status"
```

**Manual Check (One-time):**
```bash
curl -X POST "http://localhost:8000/api/youtube/monitor/check"
```

**Stop Monitoring:**
```bash
curl -X POST "http://localhost:8000/api/youtube/monitor/stop"
```

### Option 2: Command Line

**Run Once:**
```bash
python youtube_monitor.py --channel-username "@ConnectedData" --once
```

**Run Continuously:**
```bash
python youtube_monitor.py --channel-username "@ConnectedData" --check-interval 60
```

**With Channel ID:**
```bash
python youtube_monitor.py --channel-id "UC..." --check-interval 60
```

## How It Works

1. **Channel Monitoring**
   - Checks YouTube channel for new videos (default: last 24 hours)
   - Uses YouTube Data API to fetch video list
   - Tracks processed videos in `youtube_monitor_state.json`

2. **Video Processing Pipeline**
   - Downloads video metadata and subtitles
   - Falls back to Whisper audio transcription if no subtitles
   - Extracts transcript with timestamps
   - Runs NER to identify entities (people, organizations, products)
   - Extracts key concepts and topics
   - Recognizes video intent (educational, conference talk, etc.)
   - Extracts contextual information (questions, technical terms, key moments)

3. **Knowledge Graph Integration**
   - Creates Talk node with full transcript
   - Links Speaker nodes
   - Creates Tag nodes
   - Creates Entity nodes (Person, Organization, Product)
   - Creates Concept nodes with relationships
   - Stores intent and context metadata
   - Generates embeddings for semantic search

## Features

### Named Entity Recognition (NER)
- **Person**: Speakers, mentioned people
- **Organization**: Companies, institutions
- **Product**: Products, tools, technologies
- **Event**: Conferences, events
- **Location**: Places mentioned

### Intent Recognition
Classifies videos into categories:
- Educational/Tutorial
- Conference/Talk
- Product Demo
- Interview
- News/Update
- Entertainment
- Research/Academic

### Context Extraction
- Key moments (important segments)
- Technical terms
- Questions asked
- Conclusions
- Total duration

## State Management

The system maintains state in `youtube_monitor_state.json`:
```json
{
  "video_id_1": {
    "status": "completed",
    "title": "Video Title",
    "url": "https://...",
    "started_at": "2024-01-01T12:00:00",
    "completed_at": "2024-01-01T12:05:00"
  }
}
```

## Troubleshooting

### YouTube API Quota
- Free tier: 10,000 units/day
- Each video list request: ~1 unit
- If quota exceeded, wait 24 hours or upgrade

### spaCy Model Not Found
```bash
python -m spacy download en_core_web_sm
```

### Whisper Not Available
```bash
pip install openai-whisper
# Also need ffmpeg:
# macOS: brew install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg
```

### Channel Not Found
- Try using channel username: `@ConnectedData`
- Or find channel ID from YouTube channel page URL
- Channel ID format: `UC...` (starts with UC)

## Monitoring

Check logs for:
- New videos found
- Processing status
- Errors
- Entity extraction results
- Intent classification

## API Response Examples

**Start Monitoring:**
```json
{
  "status": "started",
  "message": "YouTube monitoring started",
  "monitoring_status": {
    "enabled": true,
    "channel_username": "@ConnectedData",
    "check_interval_minutes": 60
  }
}
```

**Check Status:**
```json
{
  "status": "completed",
  "new_videos_found": 2,
  "successful": 2,
  "failed": 0,
  "videos": [...]
}
```

