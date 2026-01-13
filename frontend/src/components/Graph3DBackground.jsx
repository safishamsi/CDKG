import React, { useRef, useEffect, useState, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Line } from '@react-three/drei'
import * as THREE from 'three'
import { getGraphData } from '../utils/api'
import './Graph3DBackground.css'

// 3D Node component with enhanced animations
function Node3D({ position, color, size = 0.3, index = 0 }) {
  const meshRef = useRef()
  const initialPosition = useRef([...position])
  
  useFrame((state) => {
    if (meshRef.current) {
      const time = state.clock.elapsedTime
      const offset = index * 0.5
      
      // Multi-axis floating animation
      meshRef.current.position.x = initialPosition.current[0] + Math.sin(time * 0.5 + offset) * 0.2
      meshRef.current.position.y = initialPosition.current[1] + Math.cos(time * 0.7 + offset) * 0.2
      meshRef.current.position.z = initialPosition.current[2] + Math.sin(time * 0.6 + offset) * 0.15
      
      // Gentle rotation
      meshRef.current.rotation.y += 0.003
      meshRef.current.rotation.x += 0.002
      
      // Pulsing scale effect
      const scale = 1 + Math.sin(time * 2 + offset) * 0.1
      meshRef.current.scale.set(scale, scale, scale)
    }
  })
  
  return (
    <mesh ref={meshRef} position={initialPosition.current}>
      <sphereGeometry args={[size, 16, 16]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={1.0}
        opacity={0.9}
        transparent
        metalness={0.2}
        roughness={0.1}
      />
    </mesh>
  )
}

// 3D Edge/Connection component with animation
function Edge3D({ start, end, color = '#666666', index = 0 }) {
  const lineRef = useRef()
  const points = [new THREE.Vector3(...start), new THREE.Vector3(...end)]
  
  useFrame((state) => {
    if (lineRef.current && lineRef.current.material) {
      // Subtle opacity animation
      const opacity = 0.15 + Math.sin(state.clock.elapsedTime * 0.5 + index) * 0.08
      lineRef.current.material.opacity = opacity
    }
  })
  
  return (
    <Line
      ref={lineRef}
      points={points}
      color={color}
      lineWidth={1}
    />
  )
}

// Main 3D Graph Scene
function Graph3DScene({ graphData }) {
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  
  useEffect(() => {
    if (graphData && graphData.nodes && graphData.nodes.length > 0) {
      // Use provided graph data
      setNodes(graphData.nodes)
      setEdges(graphData.links || [])
    } else {
      // Always load default graph data if no data provided
      loadGraphData()
    }
  }, [graphData])
  
  // Load graph data on mount
  useEffect(() => {
    loadGraphData()
  }, [])
  
  const loadGraphData = async () => {
    try {
      const data = await getGraphData(null, 30, 1)
      if (data && data.nodes && data.nodes.length > 0) {
        setNodes(data.nodes)
        setEdges(data.links || [])
      } else {
        // Fallback: create some default nodes if API fails
        console.log('No graph data, using fallback nodes')
        setNodes([
          { id: 'node1', name: 'Knowledge Graph', group: 1 },
          { id: 'node2', name: 'Speaker', group: 2 },
          { id: 'node3', name: 'Talk', group: 3 },
          { id: 'node4', name: 'Tag', group: 1 },
          { id: 'node5', name: 'Event', group: 4 }
        ])
        setEdges([
          { source: 'node2', target: 'node3' },
          { source: 'node3', target: 'node4' },
          { source: 'node3', target: 'node1' }
        ])
      }
    } catch (error) {
      console.error('Failed to load graph data:', error)
      // Fallback nodes
      setNodes([
        { id: 'node1', name: 'Knowledge Graph', group: 1 },
        { id: 'node2', name: 'Speaker', group: 2 },
        { id: 'node3', name: 'Talk', group: 3 }
      ])
      setEdges([
        { source: 'node2', target: 'node3' }
      ])
    }
  }
  
  // Position nodes in 3D space with better distribution
  const nodePositions = useMemo(() => {
    if (nodes.length === 0) return []
    
    return nodes.map((node, i) => {
      // Create a more organic 3D distribution
      const angle = (i / Math.max(nodes.length, 1)) * Math.PI * 2
      const radius = 2.5 + (i % 3) * 1.5
      const height = (Math.sin(i) - 0.5) * 4
      const spiral = i * 0.3 // Spiral effect
      
      return [
        Math.cos(angle + spiral) * radius,
        height,
        Math.sin(angle + spiral) * radius
      ]
    })
  }, [nodes])
  
  // Get color based on node type/group - all green variations
  const getNodeColor = (node) => {
    const group = node.group || 1
    switch (group) {
      case 1: return '#22cc66' // Light Green
      case 2: return '#2dd47e' // Medium Green
      case 3: return '#228b22' // Forest Green
      case 4: return '#32cd32' // Lime Green
      case 5: return '#3cb371' // Medium Sea Green
      default: return '#228b22' // Default Green
    }
  }
  
  // Create node map for edge connections
  const nodeMap = {}
  nodes.forEach((node, i) => {
    nodeMap[node.id] = i
  })
  
  return (
    <>
      {/* Ambient light */}
      <ambientLight intensity={0.4} />
      
      {/* Directional lights */}
      <directionalLight position={[10, 10, 5]} intensity={0.6} />
      <directionalLight position={[-10, -10, -5]} intensity={0.3} />
      
      {/* Point lights for glow effect - green */}
      <pointLight position={[5, 5, 5]} intensity={0.6} color="#22cc66" />
      <pointLight position={[-5, -5, -5]} intensity={0.6} color="#228b22" />
      
      {/* Render edges */}
      {edges.length > 0 && nodePositions.length > 0 && edges.slice(0, 100).map((edge, i) => {
        const sourceIdx = nodeMap[edge.source]
        const targetIdx = nodeMap[edge.target]
        if (sourceIdx !== undefined && targetIdx !== undefined && 
            sourceIdx < nodePositions.length && targetIdx < nodePositions.length) {
          return (
            <Edge3D
              key={i}
              start={nodePositions[sourceIdx]}
              end={nodePositions[targetIdx]}
              color="#666666"
              index={i}
            />
          )
        }
        return null
      })}
      
      {/* Render nodes */}
      {nodes.length > 0 && nodePositions.length > 0 && nodes.map((node, i) => {
        if (i >= nodePositions.length) return null
        return (
          <Node3D
            key={node.id || i}
            position={nodePositions[i]}
            color={getNodeColor(node)}
            size={0.2 + (node.value || 1) * 0.1}
            index={i}
          />
        )
      })}
      
      {/* Camera controls with slow auto-rotation - disabled interaction */}
      <OrbitControls
        enableZoom={false}
        enablePan={false}
        enableRotate={false}
        autoRotate
        autoRotateSpeed={0.3}
        minPolarAngle={Math.PI / 3}
        maxPolarAngle={Math.PI / 2.2}
        dampingFactor={0.05}
      />
    </>
  )
}

// Main 3D Background Component
function Graph3DBackground({ graphData }) {
  useEffect(() => {
    console.log('Graph3DBackground mounted, graphData:', graphData)
  }, [graphData])
  
  return (
    <div className="graph-3d-background">
      <Canvas
        camera={{ position: [0, 0, 10], fov: 50 }}
        gl={{ alpha: true, antialias: true }}
        style={{ width: '100%', height: '100%', pointerEvents: 'none' }}
      >
        <Graph3DScene graphData={graphData} />
      </Canvas>
    </div>
  )
}

export default Graph3DBackground

