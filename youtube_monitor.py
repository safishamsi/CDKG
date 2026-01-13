"""
YouTube Channel Monitor - Automatically monitor and process new videos

This module:
1. Monitors a YouTube channel for new videos
2. Automatically processes new videos with NER, context, and intent recognition
3. Runs as a background service
"""

import os
import time
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from youtube_processor import YouTubeVideoProcessor
from config import config


class YouTubeChannelMonitor:
    """Monitor YouTube channel and auto-process new videos"""
    
    def __init__(self, channel_id: Optional[str] = None, channel_username: Optional[str] = None):
        """
        Initialize YouTube channel monitor
        
        Args:
            channel_id: YouTube channel ID (e.g., 'UC...')
            channel_username: YouTube channel username/handle (e.g., '@ConnectedData' or 'ConnectedData')
        """
        self.channel_id = channel_id
        self.channel_username = channel_username
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        
        if not self.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY environment variable not set")
        
        # Initialize YouTube API client
        self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
        
        # Initialize processor
        self.processor = YouTubeVideoProcessor()
        
        # State file to track processed videos
        self.state_file = Path("youtube_monitor_state.json")
        self.processed_videos = self._load_state()
        
        # Monitoring control
        self._stop_monitoring = False
        
        # Get channel ID if username provided
        if channel_username and not channel_id:
            self.channel_id = self._get_channel_id_from_username(channel_username)
    
    def stop(self):
        """Stop the monitoring loop"""
        self._stop_monitoring = True
    
    def _load_state(self) -> Dict[str, Dict]:
        """Load state of processed videos"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading state: {e}")
                return {}
        return {}
    
    def _save_state(self):
        """Save state of processed videos"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.processed_videos, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error saving state: {e}")
    
    def _get_channel_id_from_username(self, username: str) -> Optional[str]:
        """Get channel ID from username"""
        try:
            # Remove @ if present
            username = username.lstrip('@')
            
            # Try to get channel by username
            request = self.youtube.channels().list(
                part='id',
                forUsername=username
            )
            response = request.execute()
            
            if response.get('items'):
                channel_id = response['items'][0]['id']
                print(f"✅ Found channel ID: {channel_id} for username: {username}")
                return channel_id
            
            # If not found, try searching
            request = self.youtube.search().list(
                part='snippet',
                q=username,
                type='channel',
                maxResults=1
            )
            response = request.execute()
            
            if response.get('items'):
                channel_id = response['items'][0]['snippet']['channelId']
                print(f"✅ Found channel ID: {channel_id} for username: {username}")
                return channel_id
            
            print(f"❌ Could not find channel ID for username: {username}")
            return None
            
        except HttpError as e:
            print(f"❌ Error getting channel ID: {e}")
            return None
    
    def get_channel_videos(self, max_results: int = 50, published_after: Optional[datetime] = None) -> List[Dict]:
        """
        Get recent videos from the channel
        
        Args:
            max_results: Maximum number of videos to retrieve
            published_after: Only get videos published after this date
            
        Returns:
            List of video dictionaries
        """
        if not self.channel_id:
            raise ValueError("Channel ID not set")
        
        try:
            # Get uploads playlist ID
            request = self.youtube.channels().list(
                part='contentDetails',
                id=self.channel_id
            )
            response = request.execute()
            
            if not response.get('items'):
                print(f"❌ Channel not found: {self.channel_id}")
                return []
            
            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get videos from uploads playlist
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                request = self.youtube.playlistItems().list(
                    part='snippet,contentDetails',
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                )
                response = request.execute()
                
                for item in response.get('items', []):
                    video_id = item['contentDetails']['videoId']
                    snippet = item['snippet']
                    
                    published_at = datetime.fromisoformat(
                        snippet['publishedAt'].replace('Z', '+00:00')
                    )
                    
                    # Filter by date if specified
                    if published_after and published_at < published_after:
                        continue
                    
                    video_info = {
                        'video_id': video_id,
                        'title': snippet['title'],
                        'description': snippet.get('description', ''),
                        'published_at': published_at.isoformat(),
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', '')
                    }
                    
                    videos.append(video_info)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return videos
            
        except HttpError as e:
            print(f"❌ Error fetching videos: {e}")
            return []
    
    def check_for_new_videos(self, lookback_hours: int = 24) -> List[Dict]:
        """
        Check for new videos that haven't been processed
        
        Args:
            lookback_hours: How many hours back to check
            
        Returns:
            List of new video dictionaries
        """
        print(f"\n🔍 Checking for new videos (last {lookback_hours} hours)...")
        
        published_after = datetime.now() - timedelta(hours=lookback_hours)
        all_videos = self.get_channel_videos(max_results=100, published_after=published_after)
        
        new_videos = []
        for video in all_videos:
            video_id = video['video_id']
            
            # Check if already processed
            if video_id not in self.processed_videos:
                new_videos.append(video)
            elif self.processed_videos[video_id].get('status') != 'completed':
                # Retry failed videos
                new_videos.append(video)
        
        print(f"   ✅ Found {len(new_videos)} new videos")
        return new_videos
    
    def process_new_videos(self, videos: List[Dict]) -> Dict[str, bool]:
        """
        Process new videos with enhanced NER, context, and intent recognition
        
        Args:
            videos: List of video dictionaries
            
        Returns:
            Dictionary mapping video_id to success status
        """
        results = {}
        
        for video in videos:
            video_id = video['video_id']
            url = video['url']
            
            print(f"\n{'='*70}")
            print(f"🎬 Processing: {video['title']}")
            print(f"{'='*70}")
            
            try:
                # Mark as processing
                self.processed_videos[video_id] = {
                    'status': 'processing',
                    'title': video['title'],
                    'url': url,
                    'started_at': datetime.now().isoformat()
                }
                self._save_state()
                
                # Process video (this will include NER, context, intent recognition)
                success = self.processor.process_youtube_url(url)
                
                if success:
                    self.processed_videos[video_id] = {
                        'status': 'completed',
                        'title': video['title'],
                        'url': url,
                        'started_at': self.processed_videos[video_id]['started_at'],
                        'completed_at': datetime.now().isoformat()
                    }
                    results[video_id] = True
                    print(f"✅ Successfully processed: {video['title']}")
                else:
                    self.processed_videos[video_id] = {
                        'status': 'failed',
                        'title': video['title'],
                        'url': url,
                        'started_at': self.processed_videos[video_id]['started_at'],
                        'error': 'Processing failed'
                    }
                    results[video_id] = False
                    print(f"❌ Failed to process: {video['title']}")
                
                self._save_state()
                
            except Exception as e:
                print(f"❌ Error processing {video_id}: {e}")
                self.processed_videos[video_id] = {
                    'status': 'failed',
                    'title': video['title'],
                    'url': url,
                    'error': str(e)
                }
                results[video_id] = False
                self._save_state()
        
        return results
    
    def run_continuous(self, check_interval_minutes: int = 60, lookback_hours: int = 24):
        """
        Run continuous monitoring loop
        
        Args:
            check_interval_minutes: Minutes between checks
            lookback_hours: Hours to look back for new videos
        """
        print(f"\n{'='*70}")
        print(f"🚀 Starting YouTube Channel Monitor")
        print(f"{'='*70}")
        print(f"   Channel ID: {self.channel_id}")
        print(f"   Check interval: {check_interval_minutes} minutes")
        print(f"   Lookback window: {lookback_hours} hours")
        print(f"{'='*70}\n")
        
        self._stop_monitoring = False
        
        while not self._stop_monitoring:
            try:
                # Check for new videos
                new_videos = self.check_for_new_videos(lookback_hours=lookback_hours)
                
                if new_videos:
                    print(f"\n📥 Found {len(new_videos)} new video(s) to process")
                    results = self.process_new_videos(new_videos)
                    
                    successful = sum(results.values())
                    failed = len(results) - successful
                    
                    print(f"\n📊 Processing Summary:")
                    print(f"   ✅ Successful: {successful}")
                    print(f"   ❌ Failed: {failed}")
                else:
                    print("   ℹ️  No new videos found")
                
                # Wait before next check
                print(f"\n⏳ Waiting {check_interval_minutes} minutes until next check...")
                time.sleep(check_interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping monitor...")
                break
            except Exception as e:
                print(f"\n❌ Error in monitoring loop: {e}")
                import traceback
                traceback.print_exc()
                print(f"\n⏳ Waiting {check_interval_minutes} minutes before retry...")
                time.sleep(check_interval_minutes * 60)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor YouTube channel for new videos')
    parser.add_argument('--channel-id', type=str, help='YouTube channel ID')
    parser.add_argument('--channel-username', type=str, help='YouTube channel username (e.g., @ConnectedData)')
    parser.add_argument('--check-interval', type=int, default=60, help='Check interval in minutes (default: 60)')
    parser.add_argument('--lookback-hours', type=int, default=24, help='Lookback window in hours (default: 24)')
    parser.add_argument('--once', action='store_true', help='Run once instead of continuously')
    
    args = parser.parse_args()
    
    if not args.channel_id and not args.channel_username:
        # Default to Connected Data channel
        args.channel_username = "@ConnectedData"
        print("ℹ️  No channel specified, using default: @ConnectedData")
    
    monitor = YouTubeChannelMonitor(
        channel_id=args.channel_id,
        channel_username=args.channel_username
    )
    
    if args.once:
        # Run once
        new_videos = monitor.check_for_new_videos(lookback_hours=args.lookback_hours)
        if new_videos:
            monitor.process_new_videos(new_videos)
        else:
            print("No new videos found")
    else:
        # Run continuously
        monitor.run_continuous(
            check_interval_minutes=args.check_interval,
            lookback_hours=args.lookback_hours
        )


if __name__ == "__main__":
    main()

