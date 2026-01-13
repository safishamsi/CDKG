import React, { useState } from 'react'
import Chatbot from './components/Chatbot'
import GraphVisualization from './components/GraphVisualization'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [graphData, setGraphData] = useState(null)

  return (
    <div className="App">
      <div className="animated-background"></div>
      <header className="App-header">
        <h1>CDKG RAG Chatbot</h1>
        <p>Ask questions about Connected Data World talks, speakers, and knowledge graphs</p>
      </header>
      <nav className="App-nav">
        <button 
          className={activeTab === 'chat' ? 'active' : ''}
          onClick={() => setActiveTab('chat')}
        >
          Chat
        </button>
        <button 
          className={activeTab === 'graph' ? 'active' : ''}
          onClick={() => setActiveTab('graph')}
        >
          Knowledge Graph
        </button>
      </nav>
      <main>
        {activeTab === 'chat' ? (
          <Chatbot onGraphDataUpdate={setGraphData} />
        ) : (
          <GraphVisualization data={graphData} />
        )}
      </main>
    </div>
  )
}

export default App

