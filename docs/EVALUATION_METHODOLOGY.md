# Evaluation Methodology & Grounding Standards

## 1. Principles
- **Ground Truth is Human Judged**: Automated metrics provide signal, not ground truth.
- **Reproducibility**: Every metric is calculated by code from versioned benchmarks and stored datasets.
- **No Fabricated Scores**: The UI displays pending states when no experiment has been executed.

## 2. Metrics Definition
- **Precision@K**: Fraction of top-K results with relevance ≥ 1.
- **Recall@K**: Fraction of all relevant papers captured in top-K.
- **MRR (Mean Reciprocal Rank)**: 1 / rank of first relevant paper.
- **nDCG@K**: Graded relevance discounted gain normalized against ideal ranking.
- **MAP**: Mean Average Precision across evaluated queries.

## 3. RAG Grounding Verification
1. **Layer 1 (Structural)**: Ensures chunk exists in retrieved candidate set.
2. **Layer 2 (Semantic)**: Verifies text entailment and semantic support.
