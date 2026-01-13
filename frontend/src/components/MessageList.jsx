import React from 'react'
import Message from './Message'
import LoadingIndicator from './LoadingIndicator'
import './MessageList.css'

function MessageList({ messages, isLoading, messagesEndRef }) {
  return (
    <div className="message-list">
      <div className="messages-container">
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}
        {isLoading && <LoadingIndicator />}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

export default MessageList

