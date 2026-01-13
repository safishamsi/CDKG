import React, { useState } from 'react'
import './Message.css'

// Helper function to find video link for a timestamp
function findVideoLinkForTimestamp(timestamp, sources) {
  if (!sources) return null
  
  // Parse timestamp to seconds for matching
  const parseTimestamp = (ts) => {
    const parts = ts.split(':').map(Number)
    if (parts.length === 2) {
      return parts[0] * 60 + parts[1]
    } else if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2]
    }
    return null
  }
  
  const targetSeconds = parseTimestamp(timestamp)
  if (targetSeconds === null) return null
  
  // Find transcript source with closest timestamp
  for (const source of sources) {
    if (source.type === 'transcript' && source.video_link) {
      // If we have a video_link, use it
      return source.video_link
    } else if (source.type === 'transcript' && source.video_url && source.timestamp_seconds) {
      // Build link from video_url and timestamp
      const videoUrl = source.video_url
      const urlSeconds = source.timestamp_seconds || targetSeconds
      if (videoUrl.includes('youtube.com')) {
        // Extract video ID if needed
        const videoIdMatch = videoUrl.match(/(?:v=|youtu\.be\/)([^&\n?#]+)/)
        if (videoIdMatch) {
          return `https://www.youtube.com/watch?v=${videoIdMatch[1]}&t=${Math.floor(urlSeconds)}s`
        }
      }
      return `${videoUrl}&t=${Math.floor(urlSeconds)}s`
    }
  }
  
  return null
}

function Message({ message }) {
  const [showMetadata, setShowMetadata] = useState(false)
  const isUser = message.type === 'user'
  const isError = message.isError

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-bot'} ${isError ? 'message-error' : ''}`}>
      <div className="message-content">
        <div className="message-text">
          {message.text.split('\n').map((line, i) => {
            // Clean up unwanted technical notation
            let cleanedLine = line
              .replace(/\(([^)]*)_-\[([^\]]*)\]-\_\(([^)]*)\)/g, '$1 $2 $3')
              .replace(/\(DataCatalog\)_-\s*\[poweredBy\]-\s*_\(KnowledgeGraph\)/gi, 'DataCatalog powered by Knowledge Graph')
              .replace(/_-\[/g, ' ')
              .replace(/\]-_/g, ' ')
              .trim()
            
            // Remove markdown bold syntax
            cleanedLine = cleanedLine.replace(/\*\*/g, '')
            cleanedLine = cleanedLine.replace(/__/g, '')
            
            // Format section headers (text ending with colon, or ALL CAPS)
            if (cleanedLine.match(/^[A-Z][^:]*:$/) || cleanedLine.match(/^[A-Z\s]{3,}:?$/)) {
              return <p key={i} className="message-header">{cleanedLine}</p>
            }
            
            // Format bullet points
            if (cleanedLine.match(/^[-*]\s+/)) {
              const bulletText = cleanedLine.replace(/^[-*]\s+/, '')
              // Highlight important terms in bullet points
              const parts = bulletText.split(/(\b[A-Z][a-z]+ [A-Z][a-z]+\b|\b[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+\b|"[^"]+")/g)
              return (
                <p key={i} className="message-bullet">
                  {parts.map((part, j) => {
                    // Highlight quoted titles
                    if (part.startsWith('"') && part.endsWith('"')) {
                      return <span key={j} className="highlight-title">{part}</span>
                    }
                    // Highlight speaker names
                    if (part.match(/^[A-Z][a-z]+ [A-Z][a-z]+$/) && part.length >= 5 && part.length <= 40) {
                      return <span key={j} className="highlight-name">{part}</span>
                    }
                    // Highlight talk titles
                    if (part.match(/^[A-Z][a-z]+ [A-Z][a-z]+ [A-Z]/) && part.length > 10) {
                      return <span key={j} className="highlight-title">{part}</span>
                    }
                    return part
                  })}
                </p>
              )
            }
            
            // Empty lines
            if (cleanedLine.trim() === '') {
              return <br key={i} />
            }
            
            // Regular paragraph with highlighted important terms
            // Match: timestamps, quoted titles, speaker names (First Last), talk titles (Title Case), and key phrases
            // Timestamp patterns: "at 5:23", "around 2:15", "at 10:45", "3:45", "10:00", etc.
            const timestampPattern = /(?:at|around|starting at|from|at the|near)\s*(\d{1,2}:\d{2}(?::\d{2})?|\d{1,2}:\d{2}(?::\d{2})?)\s*(?:mark|minute|second|in the video)?/gi
            const parts = cleanedLine.split(/(\d{1,2}:\d{2}(?::\d{2})?|"[^"]+"|\b[A-Z][a-z]+ [A-Z][a-z]+\b|\b[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+\b)/g)
            
            return (
              <p key={i}>
                {parts.map((part, j) => {
                  // Highlight timestamps (MM:SS or HH:MM:SS format)
                  if (part.match(/^\d{1,2}:\d{2}(?::\d{2})?$/)) {
                    // Find if there's a video link in sources for this message
                    const videoLink = findVideoLinkForTimestamp(part, message.metadata?.sources)
                    if (videoLink) {
                      return (
                        <a
                          key={j}
                          href={videoLink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="timestamp-link"
                          title={`Jump to ${part} in video`}
                        >
                          {part}
                        </a>
                      )
                    }
                    return <span key={j} className="highlight-timestamp">{part}</span>
                  }
                  // Highlight quoted titles
                  if (part.startsWith('"') && part.endsWith('"') && part.length > 3) {
                    return <span key={j} className="highlight-title">{part}</span>
                  }
                  // Highlight speaker names (First Last pattern, 5-40 chars)
                  if (part.match(/^[A-Z][a-z]+ [A-Z][a-z]+$/) && part.length >= 5 && part.length <= 40) {
                    return <span key={j} className="highlight-name">{part}</span>
                  }
                  // Highlight talk titles (Title Case with multiple words)
                  if (part.match(/^[A-Z][a-z]+ [A-Z][a-z]+ [A-Z]/) && part.length > 10 && part.length < 80) {
                    return <span key={j} className="highlight-title">{part}</span>
                  }
                  return part
                })}
              </p>
            )
          })}
        </div>
        
        {message.metadata && (
          <div className="message-metadata">
            <button 
              className="metadata-toggle"
              onClick={() => setShowMetadata(!showMetadata)}
            >
              {showMetadata ? '▼' : '▶'} Details
            </button>
            
            {showMetadata && (
              <div className="metadata-content">
                <div className="metadata-item">
                  <strong>Query Type:</strong> {message.metadata.query_type || 'N/A'}
                </div>
                
                {message.metadata.retrieval_stats && (
                  <div className="metadata-item">
                    <strong>Retrieval Stats:</strong>
                    <ul>
                      <li>Semantic: {message.metadata.retrieval_stats.semantic || 0}</li>
                      <li>Graph: {message.metadata.retrieval_stats.graph || 0}</li>
                      <li>Transcript: {message.metadata.retrieval_stats.transcript || 0}</li>
                    </ul>
                  </div>
                )}
                
                {message.metadata.sources && message.metadata.sources.length > 0 && (
                  <div className="metadata-item">
                    <strong>Sources:</strong>
                    <ul className="sources-list">
                      {message.metadata.sources.slice(0, 3).map((source, i) => (
                        <li key={i}>
                          {source.type === 'semantic' && (
                            <span>[SEMANTIC] {source.title} (score: {source.score?.toFixed(3)})</span>
                          )}
                          {source.type === 'transcript' && (
                            <span>
                              [TRANSCRIPT] {source.title}
                              {source.timestamp_display && (
                                source.video_link ? (
                                  <a 
                                    href={source.video_link} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="source-timestamp-link"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    {' '}({source.timestamp_display})
                                  </a>
                                ) : (
                                  <span className="source-timestamp"> ({source.timestamp_display})</span>
                                )
                              )}
                            </span>
                          )}
                            {source.type === 'graph' && (
                              <span>[GRAPH] {source.source} --[{source.relationship}]--&gt; {source.target}</span>
                            )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
        
        <div className="message-time">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}

export default Message

