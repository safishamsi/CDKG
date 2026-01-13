import React, { useRef, useEffect, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { getGraphData, getGraphAroundNode } from '../utils/api'
import './GraphVisualization.css'

function GraphVisualization({ data, searchQuery = null }) {
  const graphRef = useRef()
  const containerRef = useRef()
  const [graphData, setGraphData] = useState({
    nodes: [],
    links: []
  })
  const [dimensions, setDimensions] = useState({ width: 1200, height: 600 })
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [nodeSearch, setNodeSearch] = useState('')
  const [selectedNode, setSelectedNode] = useState(null)
  const [hoveredNode, setHoveredNode] = useState(null)
  const [hoveredLink, setHoveredLink] = useState(null)
  const [nodeTypeFilter, setNodeTypeFilter] = useState('all')
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)

  // Node type color mapping based on Neo4j labels
  const nodeTypeColors = {
    'Speaker': '#4a90e2',      // Blue
    'Talk': '#ff8c42',          // Orange
    'Tag': '#228b22',           // Green
    'Event': '#9b59b6',          // Purple
    'Category': '#e74c3c',      // Red
    'Organization': '#3498db',  // Light Blue
    'Product': '#f39c12',       // Yellow
    'Concept': '#1abc9c',        // Teal
    'Community': '#e67e22',      // Dark Orange
    'default': '#7ab8ff'        // Default Blue
  }

  // Node type icons/symbols
  const nodeTypeSymbols = {
    'Speaker': '👤',
    'Talk': '🎤',
    'Tag': '🏷️',
    'Event': '📅',
    'Category': '📂',
    'Organization': '🏢',
    'Product': '📦',
    'Concept': '💡',
    'Community': '👥',
    'default': '●'
  }

  // Load graph data from Neo4j
  useEffect(() => {
    const loadGraphData = async () => {
      setLoading(true)
      try {
        let result
        if (nodeSearch.trim()) {
          result = await getGraphAroundNode(nodeSearch.trim(), 2, 50)
        } else if (searchTerm.trim()) {
          result = await getGraphData(searchTerm.trim(), 100, 2)
        } else {
          result = await getGraphData(null, 150, 1)
        }
        
        if (result && result.nodes && result.nodes.length > 0) {
          // Enhance nodes with better properties
          const enhancedNodes = result.nodes.map(node => ({
            ...node,
            // Calculate node size based on connections
            connections: result.links.filter(
              link => link.source === node.id || link.target === node.id
            ).length,
            // Ensure proper type
            type: node.type || 'Unknown',
            // Set color based on type
            color: nodeTypeColors[node.type] || nodeTypeColors['default'],
            // Set symbol
            symbol: nodeTypeSymbols[node.type] || nodeTypeSymbols['default']
          }))

          setGraphData({
            nodes: enhancedNodes,
            links: result.links || []
          })
          setStats({
            totalNodes: result.total_nodes || enhancedNodes.length,
            totalLinks: result.total_links || result.links.length
          })
        } else {
          console.warn('No graph data received:', result)
          console.log('API Response:', JSON.stringify(result, null, 2))
          // Set empty data if no results
          setGraphData({ nodes: [], links: [] })
          setError(result ? 'No nodes found in response' : 'Empty response from API')
        }
      } catch (error) {
        console.error('Failed to load graph data:', error)
        console.error('Error details:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status,
          url: error.config?.url
        })
        setGraphData({ nodes: [], links: [] })
        setError(error.message || 'Failed to load graph data. Check if backend is running and VITE_API_URL is set correctly.')
        // Don't show alert, show error in UI instead
      } finally {
        setLoading(false)
      }
    }

    loadGraphData()
  }, [searchTerm, nodeSearch])

  // Use provided data if available (from chat results)
  useEffect(() => {
    if (data && data.nodes && data.nodes.length > 0) {
      const enhancedNodes = data.nodes.map(node => ({
        ...node,
        connections: data.links.filter(
          link => link.source === node.id || link.target === node.id
        ).length,
        type: node.type || 'Unknown',
        color: nodeTypeColors[node.type] || nodeTypeColors['default'],
        symbol: nodeTypeSymbols[node.type] || nodeTypeSymbols['default']
      }))
      setGraphData({
        nodes: enhancedNodes,
        links: data.links || []
      })
    }
  }, [data])

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight
        })
      }
    }
    
    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  // Filter nodes by type
  const filteredNodes = nodeTypeFilter === 'all' 
    ? graphData.nodes 
    : graphData.nodes.filter(node => node.type === nodeTypeFilter)
  
  const filteredLinks = graphData.links.filter(link => {
    const sourceNode = filteredNodes.find(n => n.id === link.source)
    const targetNode = filteredNodes.find(n => n.id === link.target)
    return sourceNode && targetNode
  })

  const displayData = {
    nodes: filteredNodes,
    links: filteredLinks
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setSearchTerm(e.target.search.value)
    setNodeSearch('')
    setSelectedNode(null)
  }

  const handleNodeSearch = (e) => {
    e.preventDefault()
    setNodeSearch(e.target.nodeSearch.value)
    setSearchTerm('')
    setSelectedNode(null)
  }

  const handleReset = () => {
    setSearchTerm('')
    setNodeSearch('')
    setSelectedNode(null)
    setNodeTypeFilter('all')
  }

  // Calculate node size based on connections
  const getNodeSize = (node) => {
    const baseSize = 8
    const connectionMultiplier = Math.sqrt(node.connections || 1) * 2
    return baseSize + connectionMultiplier
  }

  // Get unique node types for filter
  const nodeTypes = ['all', ...new Set(graphData.nodes.map(n => n.type).filter(Boolean))]

  return (
    <div className="graph-visualization">
      <div className="graph-header">
        <div className="graph-title-section">
          <h2>Knowledge Graph Visualization</h2>
          <p>Interactive Neo4j graph showing relationships between talks, speakers, and topics</p>
        </div>
        
        {stats && (
          <div className="graph-stats">
            <span className="stat-item">
              <strong>{stats.totalNodes}</strong> nodes
            </span>
            <span className="stat-item">
              <strong>{stats.totalLinks}</strong> relationships
            </span>
          </div>
        )}
        
        <div className="graph-controls">
          <form onSubmit={handleSearch} className="graph-search-form">
            <input
              type="text"
              name="search"
              placeholder="Search nodes..."
              defaultValue={searchTerm}
              className="graph-search-input"
            />
            <button type="submit" className="graph-search-button">Search</button>
          </form>
          
          <form onSubmit={handleNodeSearch} className="graph-search-form">
            <input
              type="text"
              name="nodeSearch"
              placeholder="View around node..."
              defaultValue={nodeSearch}
              className="graph-search-input"
            />
            <button type="submit" className="graph-search-button">View Around</button>
          </form>

          <select 
            value={nodeTypeFilter}
            onChange={(e) => setNodeTypeFilter(e.target.value)}
            className="graph-type-filter"
          >
            {nodeTypes.map(type => (
              <option key={type} value={type}>
                {type === 'all' ? 'All Types' : type}
              </option>
            ))}
          </select>
          
          {(searchTerm || nodeSearch || nodeTypeFilter !== 'all') && (
            <button onClick={handleReset} className="graph-reset-button">Reset</button>
          )}
        </div>
        
        {loading && <p className="graph-loading">Loading graph data from Neo4j...</p>}
        {error && (
          <div className="graph-error">
            <p>❌ {error}</p>
            <button onClick={() => { setError(null); setSearchTerm(''); setNodeSearch(''); window.location.reload(); }} className="graph-retry-button">
              Retry
            </button>
          </div>
        )}
        {displayData.nodes.length > 0 && !loading && !error && (
          <p className="graph-info">
            Showing {displayData.nodes.length} nodes and {displayData.links.length} relationships
            {nodeTypeFilter !== 'all' && ` (filtered: ${nodeTypeFilter})`}
          </p>
        )}
      </div>

      <div className="graph-container" ref={containerRef}>
        {loading ? (
          <div className="graph-loading-container">
            <p>Loading graph data from Neo4j...</p>
          </div>
        ) : error ? (
          <div className="graph-empty">
            <p style={{ color: '#e74c3c' }}>❌ {error}</p>
            <p style={{ marginTop: '1rem' }}>Make sure the backend is running and accessible.</p>
            <button onClick={() => { setError(null); setSearchTerm(''); setNodeSearch(''); window.location.reload(); }} className="graph-retry-button">
              Retry
            </button>
          </div>
        ) : displayData.nodes.length === 0 ? (
          <div className="graph-empty">
            <p>No nodes found. Try a different search or reset filters.</p>
            <button onClick={() => { setSearchTerm(''); setNodeSearch(''); setNodeTypeFilter('all'); }} className="graph-retry-button">
              Reset & Reload
            </button>
          </div>
        ) : (
          <ForceGraph2D
            ref={graphRef}
            graphData={displayData}
            nodeLabel={node => {
              const type = node.type || 'Unknown'
              const connections = node.connections || 0
              return `${node.symbol || '●'} ${node.name || node.id}\nType: ${type}\nConnections: ${connections}`
            }}
            nodeColor={node => node.color || nodeTypeColors['default']}
            nodeVal={node => getNodeSize(node)}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const label = node.name || node.id
              const fontSize = Math.max(10, 12 / globalScale)
              const nodeSize = Math.max(5, getNodeSize(node))
              
              // Draw node circle with glow effect
              ctx.shadowBlur = 15
              ctx.shadowColor = node.color || nodeTypeColors['default']
              ctx.fillStyle = node.color || nodeTypeColors['default']
              ctx.beginPath()
              ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI, false)
              ctx.fill()
              ctx.shadowBlur = 0
              
              // Draw border
              ctx.strokeStyle = node === hoveredNode ? '#ffffff' : 'rgba(255, 255, 255, 0.3)'
              ctx.lineWidth = node === hoveredNode ? 3 / globalScale : 1.5 / globalScale
              ctx.stroke()
              
              // Draw label
              if (globalScale > 0.3 && label) {
                ctx.fillStyle = '#ffffff'
                ctx.font = `bold ${fontSize}px Sans-Serif`
                ctx.textAlign = 'center'
                ctx.textBaseline = 'top'
                const textY = node.y + nodeSize + 5
                ctx.fillText(label.substring(0, 25), node.x, textY)
              }
            }}
            linkLabel={link => {
              const type = link.type || 'RELATED_TO'
              return `Relationship: ${type}`
            }}
            linkColor={link => {
              if (link === hoveredLink) return '#ffffff'
              return link.type === 'GIVES_TALK' ? '#ff8c42' :
                     link.type === 'IS_DESCRIBED_BY' ? '#228b22' :
                     link.type === 'IS_PART_OF' ? '#9b59b6' :
                     link.type === 'BELONGS_TO' ? '#e67e22' :
                     '#666666'
            }}
            linkWidth={link => {
              if (link === hoveredLink) return 3
              return link.type === 'GIVES_TALK' ? 2 : 1
            }}
            linkDirectionalArrowLength={6}
            linkDirectionalArrowRelPos={1}
            onNodeHover={node => {
              setHoveredNode(node || null)
              if (node) {
                containerRef.current.style.cursor = 'pointer'
              } else {
                containerRef.current.style.cursor = 'default'
              }
            }}
            onLinkHover={link => {
              setHoveredLink(link || null)
            }}
            onNodeClick={node => {
              setSelectedNode(node)
              console.log('Node clicked:', node)
            }}
            onLinkClick={link => {
              console.log('Link clicked:', link)
            }}
            backgroundColor="rgba(10, 10, 10, 0.95)"
            width={dimensions.width}
            height={dimensions.height}
            cooldownTicks={100}
            onEngineStop={() => {
              if (graphRef.current && displayData.nodes.length > 0) {
                setTimeout(() => {
                  graphRef.current?.zoomToFit(400, 50)
                }, 100)
              }
            }}
            enablePanInteraction={true}
            enableZoomInteraction={true}
            d3AlphaDecay={0.0228}
            d3VelocityDecay={0.4}
            nodeRelSize={6}
            minZoom={0.1}
            maxZoom={4}
          />
        )}
      </div>

      {selectedNode && (
        <div className="graph-node-details">
          <button 
            className="close-details"
            onClick={() => setSelectedNode(null)}
          >
            ×
          </button>
          <h3>{selectedNode.symbol} {selectedNode.name || selectedNode.id}</h3>
          <div className="details-content">
            <p><strong>Type:</strong> {selectedNode.type || 'Unknown'}</p>
            <p><strong>Connections:</strong> {selectedNode.connections || 0}</p>
            {selectedNode.group && <p><strong>Group:</strong> {selectedNode.group}</p>}
            {selectedNode.value && <p><strong>Value:</strong> {selectedNode.value}</p>}
          </div>
        </div>
      )}

      <div className="graph-legend">
        <div className="legend-section">
          <h4>Node Types</h4>
          <div className="legend-items">
            {Object.entries(nodeTypeColors).filter(([key]) => key !== 'default').map(([type, color]) => {
              const symbol = nodeTypeSymbols[type] || '●'
              const count = graphData.nodes.filter(n => n.type === type).length
              if (count === 0) return null
              return (
                <div key={type} className="legend-item">
                  <span className="legend-color" style={{ background: color }}>
                    {symbol}
                  </span>
                  <span>{type} ({count})</span>
                </div>
              )
            })}
          </div>
        </div>
        <div className="legend-section">
          <h4>Relationship Types</h4>
          <div className="legend-items">
            <div className="legend-item">
              <span className="legend-link" style={{ background: '#ff8c42' }}></span>
              <span>GIVES_TALK</span>
            </div>
            <div className="legend-item">
              <span className="legend-link" style={{ background: '#228b22' }}></span>
              <span>IS_DESCRIBED_BY</span>
            </div>
            <div className="legend-item">
              <span className="legend-link" style={{ background: '#9b59b6' }}></span>
              <span>IS_PART_OF</span>
            </div>
            <div className="legend-item">
              <span className="legend-link" style={{ background: '#666666' }}></span>
              <span>Other</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GraphVisualization
