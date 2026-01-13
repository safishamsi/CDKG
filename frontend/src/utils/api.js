import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

console.log('🔗 API Base URL:', API_BASE_URL)

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
})

export const queryAPI = async (query, maxHops = 2, conversationHistory = []) => {
  try {
    // Format conversation history for API
    const history = conversationHistory.map(msg => ({
      role: msg.type === 'user' ? 'user' : 'assistant',
      content: msg.text
    }))
    
    const response = await api.post('/api/query', {
      query,
      max_hops: maxHops,
      use_tools: false,
      conversation_history: history,
    })
    return response.data
  } catch (error) {
    console.error('API Error:', error)
    throw new Error(
      error.response?.data?.detail || 
      error.message || 
      'Failed to get response from server'
    )
  }
}

export const healthCheck = async () => {
  try {
    const response = await api.get('/health')
    return response.data
  } catch (error) {
    console.error('Health check failed:', error)
    return { status: 'unhealthy' }
  }
}

export const getGraphData = async (query = null, limit = 100, depth = 2) => {
  try {
    const params = { limit, depth }
    if (query) {
      params.query = query
    }
    const response = await api.get('/api/graph', { params })
    return response.data
  } catch (error) {
    console.error('Graph data fetch failed:', error)
    throw new Error(
      error.response?.data?.detail || 
      error.message || 
      'Failed to fetch graph data'
    )
  }
}

export const getGraphAroundNode = async (nodeId, depth = 2, limit = 50) => {
  try {
    const response = await api.get('/api/graph/around', {
      params: { node_id: nodeId, depth, limit }
    })
    return response.data
  } catch (error) {
    console.error('Graph around node fetch failed:', error)
    throw new Error(
      error.response?.data?.detail || 
      error.message || 
      'Failed to fetch graph around node'
    )
  }
}

export const addYouTubeVideo = async (url) => {
  try {
    const response = await api.post('/api/youtube/add', {
      url: url
    })
    return response.data
  } catch (error) {
    console.error('YouTube video add failed:', error)
    throw new Error(
      error.response?.data?.detail || 
      error.response?.data?.error ||
      error.message || 
      'Failed to add YouTube video'
    )
  }
}

export const getYouTubeJobStatus = async (jobId) => {
  try {
    const response = await api.get(`/api/youtube/status/${jobId}`)
    return response.data
  } catch (error) {
    console.error('YouTube job status fetch failed:', error)
    throw new Error(
      error.response?.data?.detail || 
      error.message || 
      'Failed to fetch job status'
    )
  }
}

export default api

