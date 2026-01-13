# CDKG RAG Chatbot Frontend

A modern React chatbot interface for the CDKG RAG system with LangGraph orchestration.

## Features

- 🎨 **Modern UI** - Beautiful gradient design with smooth animations
- 💬 **Real-time Chat** - Interactive chat interface
- 📊 **Metadata Display** - View query types, retrieval stats, and sources
- 📱 **Responsive** - Works on desktop and mobile
- ⚡ **Fast** - Built with Vite for instant hot reload

## Setup

### 1. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 2. Start Backend Server

In the project root:

```bash
# Make sure you have all Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
python backend_api.py
```

The backend will run on `http://localhost:8000`

### 3. Start Frontend Dev Server

In the `frontend` directory:

```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## Usage

1. Open `http://localhost:3000` in your browser
2. Start asking questions about Connected Data World talks, speakers, and knowledge graphs
3. Click "Details" on bot responses to see retrieval metadata

## Example Queries

- "What talks discuss knowledge graphs?"
- "What talks did Paco Nathan give?"
- "What did Paco Nathan say about graph thinking?"
- "What speakers are related to knowledge graphs?"

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Chatbot.jsx       # Main chatbot component
│   │   ├── MessageList.jsx   # Message container
│   │   ├── Message.jsx       # Individual message component
│   │   ├── InputArea.jsx    # Input form
│   │   └── LoadingIndicator.jsx
│   ├── utils/
│   │   └── api.js           # API client
│   ├── App.jsx              # Main app component
│   └── main.jsx             # Entry point
├── package.json
└── vite.config.js
```

## API Endpoints

The backend exposes:

- `GET /` - Health check
- `GET /health` - System status
- `POST /api/query` - Process chat query

## Building for Production

```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`

## Environment Variables

Create a `.env` file in the `frontend` directory:

```env
VITE_API_URL=http://localhost:8000
```

