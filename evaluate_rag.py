"""
RAG System Evaluation Script

Evaluates RAG system performance using:
- NDCG (Normalized Discounted Cumulative Gain) for retrieval ranking
- Semantic similarity for answer quality
- ROUGE scores for text overlap
- BLEU scores for n-gram matching
- Exact match and F1 scores

Uses QA/CDKGQA.csv as ground truth.
"""

import csv
import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path
from sentence_transformers import SentenceTransformer
from collections import Counter
import re

# Optional imports for advanced metrics
try:
    from rouge_score import rouge_scorer
    ROUGE_AVAILABLE = True
except ImportError:
    ROUGE_AVAILABLE = False
    print("⚠️  rouge-score not installed. Install with: pip install rouge-score")

try:
    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
    from nltk.tokenize import word_tokenize
    import nltk
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    BLEU_AVAILABLE = True
except ImportError:
    BLEU_AVAILABLE = False
    print("⚠️  nltk not installed. Install with: pip install nltk")

from rag_system import RAGSystem
from config import config


class RAGEvaluator:
    """Evaluates RAG system performance"""
    
    def __init__(self):
        """Initialize evaluator"""
        print("🚀 Initializing RAG Evaluator...")
        
        # Initialize RAG system
        self.rag = RAGSystem()
        
        # Initialize embedding model for semantic similarity
        print("   Loading embedding model for semantic similarity...")
        self.embedding_model = SentenceTransformer(
            config.embedding.model_name,
            device=config.embedding.device
        )
        
        # Initialize ROUGE scorer if available
        if ROUGE_AVAILABLE:
            self.rouge_scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        
        print("   ✅ Evaluator ready!\n")
    
    def load_qa_dataset(self, csv_path: str = "QA/CDKGQA.csv") -> List[Dict]:
        """Load QA dataset from CSV"""
        qa_pairs = []
        
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"QA dataset not found: {csv_path}")
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                question = row.get('Question', '').strip()
                baseline_answer = row.get('Baseline answer', '').strip()
                
                if question and baseline_answer:
                    qa_pairs.append({
                        'question': question,
                        'baseline_answer': baseline_answer
                    })
        
        print(f"📊 Loaded {len(qa_pairs)} QA pairs from {csv_path}\n")
        return qa_pairs
    
    def calculate_ndcg(self, relevance_scores: List[float], k: int = None) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain (NDCG)
        
        Args:
            relevance_scores: List of relevance scores (higher is better)
            k: Cutoff position (None = use all)
            
        Returns:
            NDCG score (0.0 to 1.0)
        """
        if k is None:
            k = len(relevance_scores)
        
        if k == 0:
            return 0.0
        
        # Sort scores in descending order for ideal DCG
        ideal_scores = sorted(relevance_scores, reverse=True)[:k]
        
        # Calculate DCG for actual ranking
        dcg = sum(score / np.log2(i + 2) for i, score in enumerate(relevance_scores[:k]))
        
        # Calculate ideal DCG
        idcg = sum(score / np.log2(i + 2) for i, score in enumerate(ideal_scores))
        
        # NDCG = DCG / IDCG
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between embeddings"""
        if not text1 or not text2:
            return 0.0
        
        emb1 = self.embedding_model.encode(text1, convert_to_numpy=True, normalize_embeddings=True)
        emb2 = self.embedding_model.encode(text2, convert_to_numpy=True, normalize_embeddings=True)
        
        similarity = np.dot(emb1, emb2)
        return float(similarity)
    
    def calculate_rouge_scores(self, generated: str, reference: str) -> Dict[str, float]:
        """Calculate ROUGE scores"""
        if not ROUGE_AVAILABLE:
            return {}
        
        scores = self.rouge_scorer.score(reference, generated)
        return {
            'rouge1': scores['rouge1'].fmeasure,
            'rouge2': scores['rouge2'].fmeasure,
            'rougeL': scores['rougeL'].fmeasure
        }
    
    def calculate_bleu_score(self, generated: str, reference: str) -> float:
        """Calculate BLEU score"""
        if not BLEU_AVAILABLE:
            return 0.0
        
        try:
            ref_tokens = word_tokenize(reference.lower())
            gen_tokens = word_tokenize(generated.lower())
            
            smoothing = SmoothingFunction().method1
            score = sentence_bleu([ref_tokens], gen_tokens, smoothing_function=smoothing)
            return float(score)
        except:
            return 0.0
    
    def calculate_f1_score(self, generated: str, reference: str) -> float:
        """Calculate F1 score based on token overlap"""
        gen_tokens = set(generated.lower().split())
        ref_tokens = set(reference.lower().split())
        
        if not gen_tokens or not ref_tokens:
            return 0.0
        
        intersection = gen_tokens & ref_tokens
        
        if not intersection:
            return 0.0
        
        precision = len(intersection) / len(gen_tokens)
        recall = len(intersection) / len(ref_tokens)
        
        if precision + recall == 0:
            return 0.0
        
        f1 = 2 * (precision * recall) / (precision + recall)
        return f1
    
    def calculate_exact_match(self, generated: str, reference: str) -> float:
        """Calculate exact match (1.0 if identical, 0.0 otherwise)"""
        return 1.0 if generated.strip().lower() == reference.strip().lower() else 0.0
    
    def evaluate_retrieval_ndcg(self, query: str, retrieval_results: Dict, baseline_answer: str) -> float:
        """
        Evaluate retrieval quality using NDCG
        
        Args:
            query: User query
            retrieval_results: Results from hybrid_retrieve
            baseline_answer: Ground truth answer
            
        Returns:
            NDCG score for retrieval ranking
        """
        # Get relevance scores for each retrieved result
        relevance_scores = []
        
        # Score semantic results
        for result in retrieval_results.get('semantic_results', []):
            # Use similarity score as relevance indicator
            score = result.get('similarity_score', 0.0)
            relevance_scores.append(score)
        
        # Score transcript results (check if they contain relevant content)
        for result in retrieval_results.get('transcript_results', []):
            snippet = result.get('transcript_snippet', '')
            if snippet:
                # Calculate semantic similarity to baseline answer
                similarity = self.calculate_semantic_similarity(snippet, baseline_answer)
                relevance_scores.append(similarity)
        
        # Calculate NDCG@10
        if not relevance_scores:
            return 0.0
        
        ndcg = self.calculate_ndcg(relevance_scores, k=10)
        return ndcg
    
    def evaluate_answer_quality(self, generated_answer: str, baseline_answer: str) -> Dict[str, float]:
        """Evaluate answer quality using multiple metrics"""
        metrics = {}
        
        # Semantic similarity (most important for RAG)
        metrics['semantic_similarity'] = self.calculate_semantic_similarity(
            generated_answer, baseline_answer
        )
        
        # ROUGE scores
        if ROUGE_AVAILABLE:
            rouge_scores = self.calculate_rouge_scores(generated_answer, baseline_answer)
            metrics.update(rouge_scores)
        
        # BLEU score
        if BLEU_AVAILABLE:
            metrics['bleu'] = self.calculate_bleu_score(generated_answer, baseline_answer)
        
        # F1 score
        metrics['f1'] = self.calculate_f1_score(generated_answer, baseline_answer)
        
        # Exact match
        metrics['exact_match'] = self.calculate_exact_match(generated_answer, baseline_answer)
        
        return metrics
    
    def evaluate(self, qa_pairs: List[Dict], verbose: bool = True) -> Dict:
        """
        Evaluate RAG system on QA dataset
        
        Args:
            qa_pairs: List of question-answer pairs
            verbose: Print progress
            
        Returns:
            Evaluation results dictionary
        """
        print("=" * 70)
        print("📊 Evaluating RAG System")
        print("=" * 70)
        print()
        
        all_metrics = {
            'semantic_similarity': [],
            'rouge1': [],
            'rouge2': [],
            'rougeL': [],
            'bleu': [],
            'f1': [],
            'exact_match': [],
            'ndcg': [],
            'confidence': []
        }
        
        results = []
        
        for i, qa in enumerate(qa_pairs, 1):
            question = qa['question']
            baseline_answer = qa['baseline_answer']
            
            if verbose:
                print(f"\n[{i}/{len(qa_pairs)}] Question: {question[:60]}...")
            
            try:
                # Get RAG answer
                result = self.rag.query(question, top_k=5, verbose=False)
                generated_answer = result.get('answer', '')
                retrieval_results = result.get('retrieval_results', {})
                confidence = result.get('confidence')
                
                # Evaluate answer quality
                answer_metrics = self.evaluate_answer_quality(generated_answer, baseline_answer)
                
                # Evaluate retrieval quality (NDCG)
                ndcg = self.evaluate_retrieval_ndcg(question, retrieval_results, baseline_answer)
                
                # Combine metrics
                metrics = {
                    **answer_metrics,
                    'ndcg': ndcg,
                    'confidence': confidence
                }
                
                # Add to totals
                for key in all_metrics:
                    if key in metrics:
                        all_metrics[key].append(metrics[key])
                
                results.append({
                    'question': question,
                    'baseline_answer': baseline_answer,
                    'generated_answer': generated_answer,
                    'metrics': metrics
                })
                
                if verbose:
                    print(f"   ✅ Semantic Similarity: {metrics['semantic_similarity']:.3f}")
                    print(f"   ✅ NDCG: {metrics['ndcg']:.3f}")
                    if confidence:
                        print(f"   ✅ Confidence: {confidence:.3f}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append({
                    'question': question,
                    'baseline_answer': baseline_answer,
                    'generated_answer': '',
                    'error': str(e),
                    'metrics': {}
                })
        
        # Calculate averages
        summary = {}
        for key, values in all_metrics.items():
            if values:
                summary[f'{key}_mean'] = np.mean(values)
                summary[f'{key}_std'] = np.std(values)
                summary[f'{key}_min'] = np.min(values)
                summary[f'{key}_max'] = np.max(values)
        
        return {
            'summary': summary,
            'results': results,
            'total_questions': len(qa_pairs),
            'successful_evaluations': len([r for r in results if 'error' not in r])
        }
    
    def print_report(self, evaluation_results: Dict):
        """Print evaluation report"""
        summary = evaluation_results['summary']
        results = evaluation_results['results']
        total = evaluation_results['total_questions']
        successful = evaluation_results['successful_evaluations']
        
        print("\n" + "=" * 70)
        print("📊 EVALUATION REPORT")
        print("=" * 70)
        print(f"\nTotal Questions: {total}")
        print(f"Successful Evaluations: {successful}")
        print(f"Success Rate: {successful/total*100:.1f}%")
        
        print("\n" + "-" * 70)
        print("📈 METRICS SUMMARY")
        print("-" * 70)
        
        # Primary metrics
        print("\n🎯 Primary Metrics:")
        if 'semantic_similarity_mean' in summary:
            print(f"   Semantic Similarity: {summary['semantic_similarity_mean']:.3f} ± {summary['semantic_similarity_std']:.3f}")
        if 'ndcg_mean' in summary:
            print(f"   NDCG@10:            {summary['ndcg_mean']:.3f} ± {summary['ndcg_std']:.3f}")
        
        # ROUGE scores
        if 'rouge1_mean' in summary:
            print("\n📝 ROUGE Scores:")
            print(f"   ROUGE-1:  {summary['rouge1_mean']:.3f} ± {summary['rouge1_std']:.3f}")
            print(f"   ROUGE-2:  {summary['rouge2_mean']:.3f} ± {summary['rouge2_std']:.3f}")
            print(f"   ROUGE-L:  {summary['rougeL_mean']:.3f} ± {summary['rougeL_std']:.3f}")
        
        # Other metrics
        if 'f1_mean' in summary:
            print("\n🔍 Other Metrics:")
            print(f"   F1 Score:      {summary['f1_mean']:.3f} ± {summary['f1_std']:.3f}")
            if 'bleu_mean' in summary:
                print(f"   BLEU Score:    {summary['bleu_mean']:.3f} ± {summary['bleu_std']:.3f}")
            if 'exact_match_mean' in summary:
                print(f"   Exact Match:   {summary['exact_match_mean']:.3f}")
        
        # Confidence
        if 'confidence_mean' in summary:
            print(f"\n💪 Confidence:   {summary['confidence_mean']:.3f} ± {summary['confidence_std']:.3f}")
        
        print("\n" + "=" * 70)
        
        # Show best and worst examples
        if results:
            print("\n🏆 Top 3 Best Answers (by Semantic Similarity):")
            sorted_results = sorted(
                [r for r in results if 'metrics' in r and 'semantic_similarity' in r['metrics']],
                key=lambda x: x['metrics']['semantic_similarity'],
                reverse=True
            )[:3]
            
            for i, r in enumerate(sorted_results, 1):
                sim = r['metrics']['semantic_similarity']
                print(f"\n   {i}. Similarity: {sim:.3f}")
                print(f"      Q: {r['question'][:80]}...")
                print(f"      A: {r['generated_answer'][:150]}...")
    
    def close(self):
        """Close connections"""
        if self.rag:
            self.rag.close()


def main():
    """Run evaluation"""
    evaluator = RAGEvaluator()
    
    try:
        # Load QA dataset
        qa_pairs = evaluator.load_qa_dataset()
        
        # Run evaluation
        results = evaluator.evaluate(qa_pairs, verbose=True)
        
        # Print report
        evaluator.print_report(results)
        
        # Save results to file
        import json
        output_file = Path("evaluation_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        evaluator.close()


if __name__ == "__main__":
    main()

