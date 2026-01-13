import React from 'react'
import './LoadingIndicator.css'

function LoadingIndicator() {
  return (
    <div className="loading-indicator">
      <div className="loading-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <p>Thinking...</p>
    </div>
  )
}

export default LoadingIndicator

