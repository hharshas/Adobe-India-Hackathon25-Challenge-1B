# Persona-Driven Document Intelligence - Round 1B

This solution addresses the "Connecting the Dots" challenge by creating an intelligent system that analyzes a collection of PDFs and extracts the most relevant sections based on a user persona and a specific task.

## Methodology

The approach is centered around **semantic search**, which allows the system to understand the contextual meaning of text rather than just matching keywords.

1.  **Structured PDF Parsing**: Each PDF is processed using `PyMuPDF` to extract its content. A custom parser (`pdf_parser.py`) identifies potential headings (e.g., based on bold font) and groups the subsequent text under them. This transforms each document into a series of structured "chunks" (title, content, page number).

2.  **Semantic Query Generation**: The `persona` and `job_to_be_done` fields from the input JSON are combined into a single, descriptive query string (e.g., "As a Travel Planner, I need to Plan a trip..."). This query serves as the ground truth for what the user is looking for.

3.  **Text Embedding**: The `sentence-transformers` library, specifically the `all-MiniLM-L6-v2` model, is used to convert both the query and all document chunks into numerical vectors (embeddings). This model is ideal as it's powerful, fast on a CPU, and small enough to meet the competition's constraints.

4.  **Relevance Scoring & Ranking**: Cosine similarity is computed between the query embedding and every chunk embedding. This yields a precise relevance score for each section of the documents. All sections are then ranked based on this score.

5.  **Granular Sub-Section Analysis**: For the highest-ranked sections, a deeper analysis is performed. The section's text is split into individual sentences using `nltk`. Each sentence is then semantically compared against the original query to find and extract the single most relevant sentence (`refined_text`).

6.  **Offline Capability**: The `Dockerfile` is configured to download and cache all necessary AI models (`sentence-transformers` and `nltk 'punkt'`) during the image build process. This ensures the container is fully self-contained and runs without any network access, as required.

## How to Build and Run

### Prerequisites

* Docker is installed and running on your machine.

### Build the Docker Image

1.  Place all the provided files (`main.py`, `pdf_parser.py`, `semantic_analyzer.py`, `requirements.txt`, `Dockerfile`, `README.md`) in a single directory.
2.  Open a terminal in that directory.
3.  Run the build command:

    ```bash
    docker build --platform linux/amd64 -t document-analyzer:latest .
    ```

### Run the Solution

1.  In your project directory, create two subdirectories: `input` and `output`.
2.  Place your PDF files and the main input JSON file (e.g., `travel_planner.json`) inside the `input` directory.
3.  Run the Docker container using the following command. This mounts your local `input` and `output` folders into the container.

    ```bash
    docker run --rm -v "$(pwd)/input":/app/input -v "$(pwd)/output":/app/output --network none document-analyzer:latest
    ```

The application will automatically find the JSON file in the `input` folder, process the specified PDFs, and generate a corresponding `*_output.json` file in your `output` folder.
