# CF-Coach Proposal

## Product goal

CF-Coach is a personalized Codeforces problem recommender for competitive programmers.

A user enters a Codeforces handle. The system analyzes solved problems, rating, and tag history, then recommends unsolved problems that are appropriate for the user and explains each recommendation.

## MVP

- Input a Codeforces handle.
- Retrieve profile, submissions, and a problem catalog.
- Exclude solved problems.
- Return 10 recommendations with title, rating, tags, URL, score, and a short reason.
- Use a transparent baseline score based on rating proximity and under-practiced tags.

## Out of scope for Sprint 1

- Trained ML model.
- Authentication, database, deployment, or polished UI.
- Browser extension or chatbot.

## ML direction after the MVP

Compare the baseline against a learning-to-rank or binary classification model using user/problem features such as rating gap, tag practice frequency, historical acceptance, and recency.

## Success criteria

1. The end-to-end recommendation flow works for at least three real handles.
2. Recommendations never include solved problems.
3. Every result includes an understandable reason.
4. Later ML evaluation improves over the baseline on Recall@10 and/or NDCG@10.
