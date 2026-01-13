import React, { useState, useRef, useEffect } from 'react'
import MessageList from './MessageList'
import InputArea from './InputArea'
import { queryAPI } from '../utils/api'
import './Chatbot.css'

function Chatbot({ onGraphDataUpdate }) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: "Hello! I'm your CDKG RAG assistant. I can help you find information about Connected Data World talks, speakers, and knowledge graphs. What would you like to know?",
      timestamp: new Date()
    }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (text) => {
    if (!text.trim() || isLoading) return

    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: text.trim(),
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      // Call API with conversation history (exclude the current user message we just added)
      const historyMessages = messages.filter(m => m.id !== userMessage.id)
      const response = await queryAPI(text.trim(), 2, historyMessages)
      
      // Extract graph data from response
      if (response.sources && onGraphDataUpdate) {
        const graphNodes = new Set()
        const graphLinks = []
        
        response.sources.forEach(source => {
          if (source.type === 'graph') {
            graphNodes.add(source.source)
            graphNodes.add(source.target)
            graphLinks.push({
              source: source.source,
              target: source.target,
              relationship: source.relationship
            })
          } else if (source.title) {
            graphNodes.add(source.title)
          }
        })
        
        if (graphNodes.size > 0) {
          onGraphDataUpdate({
            nodes: Array.from(graphNodes).map(name => ({ id: name, name })),
            links: graphLinks
          })
        }
      }
      
      // Add bot response
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: response.answer || 'Sorry, I could not generate an answer.',
        timestamp: new Date(),
        metadata: {
          query_type: response.query_type,
          retrieval_stats: response.retrieval_stats,
          sources: response.sources
        }
      }
      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      console.error('Error:', error)
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: `Sorry, I encountered an error: ${error.message}`,
        timestamp: new Date(),
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chatbot-container">
      <div className="chatbot-window">
        <MessageList 
          messages={messages} 
          isLoading={isLoading}
          messagesEndRef={messagesEndRef}
        />
        <InputArea 
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </div>
    </div>
  )
}

export default Chatbot

