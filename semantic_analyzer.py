import nltk
from sentence_transformers import SentenceTransformer, util

class SemanticAnalyzer:
    """
    Handles the core logic of semantic analysis:
    - Loading the embedding model.
    - Ranking sections based on relevance to a query.
    - Finding the most relevant sentence within a section.
    """
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initializes the analyzer and loads the sentence-transformer model.
        This model is chosen for its balance of performance and size, making it
        ideal for CPU-based, offline execution.
        """
        print("Loading semantic model. This may take a moment...")
        self.model = SentenceTransformer(model_name)
        print("Semantic model loaded successfully.")
        
        # Ensure the 'punkt' tokenizer for sentence splitting is available
        try:
            nltk.data.find('tokenizers/punkt')
        except nltk.downloader.DownloadError:
            print("Downloading 'punkt' for sentence tokenization...")
            nltk.download('punkt')

    def rank_sections(self, query_text, chunks):
        """
        Ranks a list of text chunks based on their semantic similarity to a query.

        Args:
            query_text (str): The combined persona and job-to-be-done.
            chunks (list): A list of dictionaries, each representing a text chunk.

        Returns:
            list: The list of chunks, sorted by relevance, with an 'importance_score' added.
        """
        if not chunks:
            return []

        print(f"Creating embeddings for {len(chunks)} document sections...")
        corpus = [chunk.get('content', '') for chunk in chunks]
        corpus_embeddings = self.model.encode(corpus, convert_to_tensor=True, show_progress_bar=False)
        
        print("Creating embedding for the query...")
        query_embedding = self.model.encode(query_text, convert_to_tensor=True)

        print("Calculating similarity scores...")
        cosine_scores = util.cos_sim(query_embedding, corpus_embeddings)

        for i, chunk in enumerate(chunks):
            chunk['importance_score'] = cosine_scores[0][i].item()

        return sorted(chunks, key=lambda x: x['importance_score'], reverse=True)

    def find_most_relevant_sentence(self, query_text, section_content):
        """
        Finds the single most relevant sentence in a block of text relative to a query.

        Args:
            query_text (str): The user's query.
            section_content (str): The content of a document section.

        Returns:
            str: The most relevant sentence found.
        """
        if not section_content or not section_content.strip():
            return "No content available in this section."

        sentences = nltk.sent_tokenize(section_content)
        if not sentences:
            return section_content # Fallback to returning the whole content if sentence splitting fails

        query_embedding = self.model.encode(query_text, convert_to_tensor=True)
        sentence_embeddings = self.model.encode(sentences, convert_to_tensor=True)

        cosine_scores = util.cos_sim(query_embedding, sentence_embeddings)
        best_sentence_index = cosine_scores.argmax()
        
        return sentences[best_sentence_index]
