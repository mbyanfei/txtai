"""
Explain module
"""

import numpy as np


class Explain:
    """
    Explains the importance of each token in an input text element for a query. This method creates n permutations of the input text, where n
    is the number of tokens in the input text. This effectively masks each token to determine its importance to the query.
    """

    def __init__(self, embeddings):
        """
        Creates a new explain action.

        Args:
            embeddings: embeddings instance
        """

        self.embeddings = embeddings
        self.content = self.embeddings.config.get("content")

    def __call__(self, queries, texts, limit):
        """
        Explains the importance of each input token in text for a list of queries.

        Args:
            query: input queries
            texts: optional list of (text|list of tokens), otherwise runs search queries
            limit: optional limit if texts is None

        Returns:
            list of dict per input text per query where a higher token scores represents higher importance relative to the query
        """

        # Construct texts elements per query
        texts = self.texts(queries, texts, limit)

        # Explain each query-texts combination
        return [self.explain(query, texts[x]) for x, query in enumerate(queries)]

    def texts(self, queries, texts, limit):
        """
        Constructs lists of dict for each input query.

        Args:
            queries: input queries
            texts: optional list of texts
            limit: optional limit if texts is None

        Returns:
            lists of dict for each input query
        """

        # Calculate similarity scores per query if texts present
        if texts:
            results = []
            for scores in self.embeddings.batchsimilarity(queries, texts):
                results.append([{"id": uid, "text": texts[uid], "score": score} for uid, score in scores])

            return results

        # Query for results if texts is None and content is enabled
        return self.embeddings.batchsearch(queries, limit) if self.content else [[]] * len(queries)

    def explain(self, query, texts):
        """
        Explains the importance of each input token in text for a list of queries.

        Args:
            query: input query
            texts: list of text

        Returns:
            list of {"id": value, "text": value, "score": value, "tokens": value} covering each input text element
        """

        # Explain results
        results = []

        # Calculate result per input text element
        for x in texts:
            text = x["text"]
            tokens = text if isinstance(text, list) else text.split()

            # Create permutations of input text, masking each token to determine importance
            permutations = []
            for i in range(len(tokens)):
                data = tokens.copy()
                data.pop(i)
                permutations.append([" ".join(data)])

            # Calculate similarity for each input text permutation and get score delta as importance
            scores = [(i, x["score"] - np.abs(s)) for i, s in self.embeddings.similarity(query, permutations)]

            # Add data sorted in index order
            results.append(
                {"id": x["id"], "text": text, "score": x["score"], "tokens": [(tokens[i], score) for i, score in sorted(scores, key=lambda x: x[0])]}
            )

        # Sort score descending and return
        return sorted(results, key=lambda x: x["score"], reverse=True)
