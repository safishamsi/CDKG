# 📊 RAG System Evaluation Guide

## Overview

The evaluation script (`evaluate_rag.py`) evaluates RAG system performance using multiple metrics, including **NDCG** as requested.

---

## 🎯 Metrics Used

### 1. **NDCG (Normalized Discounted Cumulative Gain)** ⭐
- **Purpose**: Evaluates retrieval ranking quality
- **Range**: 0.0 to 1.0 (higher is better)
- **What it measures**: How well the system ranks relevant results
- **NDCG@10**: Evaluates top 10 retrieved results

### 2. **Semantic Similarity**
- **Purpose**: Measures answer quality using embeddings
- **Range**: -1.0 to 1.0 (higher is better)
- **What it measures**: Conceptual similarity between generated and baseline answers
- **Most important** for RAG systems

### 3. **ROUGE Scores**
- **ROUGE-1**: Unigram overlap
- **ROUGE-2**: Bigram overlap
- **ROUGE-L**: Longest common subsequence
- **Range**: 0.0 to 1.0 (higher is better)

### 4. **BLEU Score**
- **Purpose**: N-gram precision matching
- **Range**: 0.0 to 1.0 (higher is better)
- **What it measures**: Text overlap quality

### 5. **F1 Score**
- **Purpose**: Token overlap balance
- **Range**: 0.0 to 1.0 (higher is better)
- **What it measures**: Precision and recall of matching tokens

### 6. **Exact Match**
- **Purpose**: Perfect answer matching
- **Range**: 0.0 or 1.0
- **What it measures**: Whether answers are identical

### 7. **Confidence Score**
- **Purpose**: System's confidence in answers
- **Range**: 0.0 to 1.0
- **What it measures**: Retrieval quality indicators

---

## 🚀 Usage

### Basic Usage

```bash
python evaluate_rag.py
```

This will:
1. Load QA questions from `QA/CDKGQA.csv`
2. Run each question through the RAG system
3. Compare generated answers to baseline answers
4. Calculate all metrics (including NDCG)
5. Print a comprehensive report
6. Save results to `evaluation_results.json`

### Prerequisites

**Required**:
- RAG system initialized (Neo4j, embeddings, etc.)
- `QA/CDKGQA.csv` file with questions and baseline answers

**Optional** (for additional metrics):
```bash
# For ROUGE scores
pip install rouge-score

# For BLEU scores
pip install nltk
```

---

## 📊 Understanding the Results

### Example Output

```
📊 EVALUATION REPORT
======================================================================
Total Questions: 12
Successful Evaluations: 12
Success Rate: 100.0%

📈 METRICS SUMMARY
----------------------------------------------------------------------

🎯 Primary Metrics:
   Semantic Similarity: 0.782 ± 0.145
   NDCG@10:            0.654 ± 0.123

📝 ROUGE Scores:
   ROUGE-1:  0.456 ± 0.089
   ROUGE-2:  0.312 ± 0.078
   ROUGE-L:  0.423 ± 0.091

🔍 Other Metrics:
   F1 Score:      0.521 ± 0.102
   BLEU Score:    0.234 ± 0.067
   Exact Match:   0.083

💪 Confidence:   0.712 ± 0.156
```

### Interpreting Scores

**NDCG@10**:
- **> 0.7**: Excellent ranking
- **0.5 - 0.7**: Good ranking
- **0.3 - 0.5**: Fair ranking
- **< 0.3**: Poor ranking

**Semantic Similarity**:
- **> 0.8**: Very similar answers
- **0.6 - 0.8**: Similar answers
- **0.4 - 0.6**: Somewhat similar
- **< 0.4**: Different answers

**ROUGE Scores**:
- **> 0.5**: Good overlap
- **0.3 - 0.5**: Moderate overlap
- **< 0.3**: Low overlap

---

## 🔧 Customization

### Evaluate Specific Questions

Modify the script to evaluate only certain questions:

```python
qa_pairs = evaluator.load_qa_dataset()
# Filter to specific questions
qa_pairs = [qa for qa in qa_pairs if "knowledge graph" in qa['question'].lower()]
results = evaluator.evaluate(qa_pairs)
```

### Change NDCG Cutoff

Modify NDCG calculation in `evaluate_retrieval_ndcg()`:

```python
# Change from NDCG@10 to NDCG@5
ndcg = self.calculate_ndcg(relevance_scores, k=5)
```

### Add Custom Metrics

Extend `evaluate_answer_quality()` to add your own metrics.

---

## 📁 Output Files

### `evaluation_results.json`

Contains:
- Summary statistics (mean, std, min, max for each metric)
- Individual results for each question
- Generated answers
- All metric scores

**Example structure**:
```json
{
  "summary": {
    "semantic_similarity_mean": 0.782,
    "ndcg_mean": 0.654,
    ...
  },
  "results": [
    {
      "question": "...",
      "baseline_answer": "...",
      "generated_answer": "...",
      "metrics": {
        "semantic_similarity": 0.85,
        "ndcg": 0.72,
        ...
      }
    }
  ]
}
```

---

## 🎯 Best Practices

1. **Run evaluation regularly**: Track improvements over time
2. **Compare metrics**: Don't rely on a single metric
3. **Check individual results**: Look at best/worst examples
4. **Monitor confidence**: Low confidence may indicate issues
5. **Update baseline answers**: Keep QA dataset current

---

## 🐛 Troubleshooting

### "QA dataset not found"
- Ensure `QA/CDKGQA.csv` exists
- Check file path in script

### "ROUGE scores not available"
- Install: `pip install rouge-score`
- Script will still work without it

### "BLEU scores not available"
- Install: `pip install nltk`
- Script will still work without it

### Low NDCG scores
- Check retrieval quality
- Verify embeddings are up to date
- Check if relevant content exists in knowledge graph

---

## 📈 Improving Scores

### To Improve NDCG:
1. Better retrieval ranking
2. Improve embeddings (include more transcript content)
3. Tune hybrid retrieval weights
4. Add more relevant content to knowledge graph

### To Improve Semantic Similarity:
1. Better answer generation prompts
2. More context in retrieval
3. Better synthesis of multiple sources
4. Improve transcript search

### To Improve ROUGE/BLEU:
1. More direct quotes from transcripts
2. Better text matching
3. Improve answer completeness

---

## 🔗 Related Files

- `evaluate_rag.py` - Main evaluation script
- `QA/CDKGQA.csv` - Ground truth questions and answers
- `rag_system.py` - RAG system being evaluated
- `langgraph_orchestrator.py` - Orchestration (affects confidence scores)

---

**Ready to evaluate?** Run `python evaluate_rag.py` and review the results! 🚀

