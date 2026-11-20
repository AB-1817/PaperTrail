from __future__ import annotations

import re


def mmr_diversity_filter(
    candidates: list[dict],
    lambda_param: float = 0.3,
    limit: int = 20,
) -> list[dict]:
    """
    Maximal Marginal Relevance (MMR) filter to promote diversity in recommendations.
    Penalizes candidates with very similar titles or abstracts to already selected ones.
    """
    if len(candidates) <= limit:
        return candidates

    selected: list[dict] = [candidates[0]]
    remaining = candidates[1:]

    def tokenize(s: str) -> set[str]:
        return set(re.findall(r"\w+", s.lower()))

    while len(selected) < limit and remaining:
        best_cand = None
        best_score = -float("inf")

        for cand in remaining:
            rel_score = cand.get("score", 0.0)
            cand_tokens = tokenize(cand.get("title", ""))

            # Compute max similarity to any already selected candidate
            max_sim = 0.0
            for sel in selected:
                sel_tokens = tokenize(sel.get("title", ""))
                union_len = len(cand_tokens | sel_tokens)
                sim = len(cand_tokens & sel_tokens) / union_len if union_len > 0 else 0.0
                if sim > max_sim:
                    max_sim = sim

            mmr_score = lambda_param * rel_score - (1 - lambda_param) * max_sim
            if mmr_score > best_score:
                best_score = mmr_score
                best_cand = cand

        if best_cand:
            selected.append(best_cand)
            remaining.remove(best_cand)
        else:
            break

    return selected
