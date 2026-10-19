"""Deterministic baseline ranking by rating proximity and tag practice."""

from __future__ import annotations

from typing import Any

UNRATED_USER_RATING = 800


def recommend(
    user_context: dict[str, Any],
    problems: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return up to limit unique, rated, unsolved RecommendationItem records.

    Score = 0.8 / (1 + rating_distance / 400) + 0.2 * mean(1 / (1 +
    tag_solve_count)). Missing tag counts mean zero practice; untagged problems
    receive no tag boost. Unrated users use an explicit starting rating of 800.
    Ties favor smaller rating distance, then lexicographic problem ID.
    """
    if type(limit) is not int or limit <= 0:
        raise ValueError("Recommendation limit must be a positive integer.")

    user_rating = user_context["rating"]
    target_rating = UNRATED_USER_RATING if user_rating is None else user_rating
    solved = set(user_context["solved_problem_ids"])
    tag_counts = user_context["tag_solve_counts"]
    seen: set[str] = set()
    ranked: list[dict[str, Any]] = []

    for problem in problems:
        problem_id = problem["problem_id"]
        rating = problem["rating"]
        if problem_id in solved or problem_id in seen or rating is None:
            continue
        seen.add(problem_id)
        tags = list(dict.fromkeys(problem["tags"]))
        distance = abs(rating - target_rating)
        tag_boost = (
            sum(1 / (1 + tag_counts.get(tag, 0)) for tag in tags) / len(tags)
            if tags
            else 0.0
        )
        score = 0.8 / (1 + distance / 400) + 0.2 * tag_boost

        if user_rating is None:
            reason = f"Unrated user: using starting rating {target_rating}. "
        else:
            reason = ""
        reason += f"Rating {rating} is {distance} from your target {target_rating}."
        if tags:
            least_practiced = min(tags, key=lambda tag: (tag_counts.get(tag, 0), tag))
            count = tag_counts.get(least_practiced, 0)
            reason += f" Practice {least_practiced} ({count} solved in your history)."
        else:
            reason += " No tags available for a practice boost."

        ranked.append(
            {
                **problem,
                "tags": tags,
                "score": score,
                "reason": reason,
            }
        )

    ranked.sort(
        key=lambda item: (
            -item["score"],
            abs(item["rating"] - target_rating),
            item["problem_id"],
        )
    )
    return ranked[:limit]
