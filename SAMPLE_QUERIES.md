# Sample Queries for CDKG RAG Chatbot

## Semantic Search Queries
These queries test semantic similarity search using vector embeddings:

1. **"What talks discuss knowledge graphs?"**
   - Tests: Semantic search, finding talks by topic
   - Expected: List of talks about knowledge graphs

2. **"What presentations cover semantic technology?"**
   - Tests: Semantic understanding of "semantic technology"
   - Expected: Talks related to semantic web, RDF, ontologies

3. **"Tell me about graph databases and their applications"**
   - Tests: Broad topic search
   - Expected: Talks covering graph database concepts

4. **"What are the main topics discussed at Connected Data World?"**
   - Tests: General topic discovery
   - Expected: Overview of conference themes

## Graph Traversal Queries
These queries test relationship traversal in the knowledge graph:

5. **"What talks did Paco Nathan give?"**
   - Tests: Graph traversal from speaker to talks
   - Expected: List of talks by Paco Nathan

6. **"What speakers presented on knowledge graphs?"**
   - Tests: Graph traversal from topic to speakers
   - Expected: Speakers who gave knowledge graph talks

7. **"Who spoke at Connected Data World 2021?"**
   - Tests: Event to speaker relationships
   - Expected: List of speakers from that event

8. **"What tags are associated with graph thinking?"**
   - Tests: Talk to tag relationships
   - Expected: Related tags and keywords

## Multi-hop Reasoning Queries
These queries test complex relationship discovery:

9. **"How is Paco Nathan related to knowledge graphs?"**
   - Tests: Multi-hop path finding
   - Expected: Path showing Paco Nathan → Talks → Knowledge Graphs

10. **"What speakers are connected to semantic technology topics?"**
    - Tests: Multi-hop reasoning
    - Expected: Speakers connected through talks and tags

11. **"Find the relationship between Juan Sequeda and data catalogs"**
    - Tests: Path finding between entities
    - Expected: Connection path

## Hybrid Queries (Transcript + Semantic + Graph)
These queries test comprehensive retrieval:

12. **"What did Paco Nathan say about graph thinking?"**
    - Tests: Transcript search + semantic + graph
    - Expected: Actual quotes from transcript with timestamps

13. **"What examples did speakers give about knowledge graphs?"**
    - Tests: Transcript content search
    - Expected: Specific examples from talk transcripts

14. **"Tell me about the village scenario mentioned in talks"**
    - Tests: Specific transcript content
    - Expected: Details about Pat, Hannah, Thomas scenario

15. **"What did speakers say about the Cynefin framework?"**
    - Tests: Transcript search for specific concepts
    - Expected: Mentions of Cynefin framework with context

## Specific Information Queries

16. **"What is the talk 'Graph Thinking' about?"**
    - Tests: Specific talk retrieval
    - Expected: Description, speaker, category, tags

17. **"Who is Juan Sequeda and what did he present?"**
    - Tests: Speaker information + related talks
    - Expected: Speaker bio and talk list

18. **"What categories of talks are available?"**
    - Tests: Category discovery
    - Expected: List of talk categories

19. **"Show me talks about data integration"**
    - Tests: Topic-based search
    - Expected: Talks related to data integration

20. **"What are the most discussed topics at the conference?"**
    - Tests: Tag/keyword analysis
    - Expected: Most common tags and topics

## Complex Analytical Queries

21. **"Compare knowledge graph talks with semantic technology talks"**
    - Tests: Comparative analysis
    - Expected: Differences and similarities

22. **"What are the main themes across all Connected Data World talks?"**
    - Tests: Broad analysis
    - Expected: High-level themes and patterns

23. **"Which speakers have given multiple talks?"**
    - Tests: Graph aggregation
    - Expected: Speakers with multiple presentations

24. **"What talks discuss both graphs and AI?"**
    - Tests: Multi-topic intersection
    - Expected: Talks covering both topics

## Quick Test Queries (Start Here)

**Begin with these simple queries:**

1. "What talks discuss knowledge graphs?"
2. "What talks did Paco Nathan give?"
3. "What did Paco Nathan say about graph thinking?"
4. "What speakers are related to knowledge graphs?"

These will quickly demonstrate the system's capabilities!

