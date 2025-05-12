# Candidate Assistant: AI-Powered RAG Chatbot for Enhanced Candidate Q&A

## Overview

This project implements an **AI-powered chatbot** utilizing a **Retrieval-Augmented Generation (RAG)** pattern to enable natural language conversations about a pool of candidates. It connects a user interface to a Large Language Model (LLM), potentially managed via tools like **Ollama** and interfaced through **Open WebUI**, allowing users to query candidate details stored in markdown files using models such as **Gemma 3**.

The core challenge addressed by this project is the **enhancement of RAG accuracy** for datasets with highly similar document structures, like candidate resumes or profiles. Standard RAG systems can struggle to differentiate between candidates when querying across the entire corpus due to structural similarities. This application tackles this by **precisely focusing the LLM's context**: instead of retrieving potentially ambiguous snippets from multiple documents, it retrieves the *entire specific document* for the selected candidate and injects it as grounding context for the LLM.

This approach transforms static candidate profiles into interactive knowledge sources, allowing users to ask specific questions and receive accurate, **document-grounded answers** from the AI assistant.

## AI Capabilities & Key Features

* **RAG Implementation:** Leverages a Retrieval-Augmented Generation pattern where candidate markdown files serve as the knowledge base.
* **Enhanced Contextual Grounding:** Overcomes typical RAG limitations with similar documents by **retrieving and injecting the full document text** for the *specifically selected candidate* into the LLM prompt. This ensures high relevance and accuracy.
* **AI-Powered Q&A:** Engage in natural language conversations with an integrated LLM (e.g., **Gemma 3 via Ollama/Open WebUI**) to ask specific questions about selected candidates.
* **Document-Grounded Responses:** The LLM is explicitly instructed to answer *only* based on the provided candidate document, minimizing hallucinations and improving factual accuracy.
* **Configurable LLM Backend:** Connects to any OpenAI-compatible API endpoint (like Open WebUI) via `.env` configuration, allowing flexibility in choosing LLM providers and models.
* **Token Usage Monitoring:** Displays key LLM token metrics and response time, providing operational insights.
* **Multi-Conversation Management:** Maintains separate, contextually isolated AI chat histories for each candidate within the user's browser session.
* **Responsive Web Interface:** Dark mode UI optimized for various screen sizes.
* **Efficient Candidate Navigation:** Dynamically loads candidates from markdown filenames and provides a searchable list.
* **Formatted Data Display:** Renders candidate markdown details accurately.
* **Containerized Deployment:** Includes `Dockerfile` and `docker-compose.yml` for easy deployment.

## RAG Implementation & Data Enhancement Strategy

This project employs a targeted RAG strategy specifically designed for querying individual entities within a homogenous dataset:

1.  **Retrieval:** Instead of complex semantic search across all documents, the "retrieval" step is simplified to fetching the *single, specific markdown document* corresponding to the candidate explicitly selected by the user in the UI.
2.  **Data Enhancement (Context Preparation):** The *key value proposition* lies here. The raw markdown content of the selected candidate's file is treated as essential metadata. It's formatted into a clear, instructional prompt (using the `CONTEXT_PROMPT_TEMPLATE` in `.env`). This "enhanced data" explicitly tells the LLM: "Here is *all* the information about Candidate X. Answer the following questions *only* based on this."
3.  **Generation:** This precisely formatted context, along with the user's actual question and the visible chat history, is sent to the LLM (e.g., Gemma 3) for response generation.

**Why this approach?** Standard vector-based RAG on many similar resumes often retrieves overlapping or irrelevant chunks, making it hard for the LLM to answer accurately about *one specific person*. By retrieving the full document and clearly scoping the LLM's task to *that document alone*, we significantly improve the accuracy and relevance of the generated answers for this specific use case.

## Architecture & AI Integration

The application orchestrates the RAG flow:

1.  **Frontend (Browser):** Manages user selection, displays data/chat, holds conversation states, sends requests to the backend.
2.  **Backend API (Flask/Python):**
    * Serves the frontend.
    * Retrieves the specific candidate document (`mdata/` file) based on user selection (the "Retrieval" step).
    * Formats the document content into the hidden instructional prompt (the "Data Enhancement" step).
    * Sends the combined context + user query + history to the LLM API.
    * Relays the LLM's response and usage stats back to the frontend.
3.  **LLM API (External - e.g., Open WebUI serving Ollama/Gemma 3):** Receives the context-enhanced prompts and generates the responses (the "Generation" step).

## Project Structure
```
rag-recruiter-chat
├── backend/
│   ├── api/                 # API Blueprints
│   │   ├── init.py
│   │   ├── candidates.py
│   │   └── chat.py
│   ├── services/            # Business Logic (LLM, Files)
│   │   ├── init.py
│   │   ├── candidate_service.py
│   │   └── chat_service.py
│   ├── static/              # CSS, JS
│   │   ├── css/style.css
│   │   └── js/main.js
│   ├── templates/           # HTML Templates
│   │   └── index.html
│   ├── utils/               # Utilities (Logging)
│   │   ├── init.py
│   │   └── logger.py
│   ├── app.py               # Flask App Factory & Runner
│   └── init.py
├── mdata/                   # Candidate Markdown Files (Mounted Volume)
│   └── Jane_Doe_2023.md     # Example
├── .env                     # Environment Variables (Gitignored)
├── scripts/                 # Data processing scripts
│   ├── s1converttocsv.py       
│   ├── s2converttojson.py       
│   ├── s3converttomd.py       
│   ├── s4convertmdtojson.py       
│   └── s5loadtprag.py
│
├── .gitignore
├── Dockerfile               # Backend Docker Image Instructions
├── docker-compose.yml       # Docker Compose Setup
└── requirements.txt         # Python Dependencies
```

## Data Preparation Pipeline

The candidate data used by this application is processed through a five-step pipeline, executed by a series of Python scripts. This pipeline transforms data from its initial Excel format into JSON files suitable for loading into the RAG system. The `mdata/` directory, which the main application uses, is an output of this pipeline (specifically, step 3).

Here's an overview of each script's role:

1.  **`s1converttocsv.py` (Excel to CSV Conversion):**
    * **Input:** An Excel file (`candidatos.xlsx`) containing the raw candidate data.
    * **Process:** Reads the active sheet from the Excel workbook. It iterates through each row and cell, extracting cell values. If a cell contains a hyperlink, its target URL is extracted; otherwise, the regular cell value is used.
    * **Output:** A CSV file (`candidatos.csv`) where each row corresponds to a candidate and columns represent their attributes.

2.  **`s2converttojson.py` (CSV to Structured JSON):**
    * **Input:** The `candidatos.csv` file generated in the previous step.
    * **Process:** Reads the CSV file row by row. For each candidate, it constructs a structured JSON object. This involves creating a detailed "Description" string by combining various fields and handling cases where data might be missing (e.g., "no reportó" or "no proporcionó"). It also creates a "Metadata" object containing key candidate details. Each candidate's data is saved as an individual JSON file.
    * **Output:** Multiple JSON files, one for each candidate, stored in a `data/` directory. The filenames are derived from the candidate's name.

3.  **`s3converttomd.py` (JSON to Markdown with LLM Tagging):**
    * **Input:** The `candidatos.csv` file (note: it re-reads the CSV, not the JSONs from step 2, to process rows directly).
    * **Process:** This is a crucial step where data is transformed into Markdown format and enriched using an LLM. For each candidate row in the CSV:
        * It pre-collects text related to education and proposals/purpose.
        * It calls an external LLM API (configured via `OPENWEBUI_API_URL`, `OPENWEBUI_TOKEN`, `OPENWEBUI_MODEL`) to:
            * Generate relevant "Tags" based on the candidate's education and academic background.
            * Generate "Tags" based on their purpose, vision, and proposals.
            * Generate a concise "Description" of the candidate's profile.
        * It then formats all the candidate's information, including the LLM-generated tags and description, into a structured Markdown file. Specific fields are presented as distinct sections with H2 headings.
    * **Output:** Markdown files (`.md`) for each candidate, saved in the `mdata/` directory. These are the files the main Candidate Assistant application reads.

4.  **`s4convertmdtojson.py` (Markdown to JSON for RAG Loading):**
    * **Input:** The Markdown files located in a `done/` directory (presumably the `mdata/` files after review/finalization are moved or copied here).
    * **Process:** Parses each Markdown file. It separates the initial metadata block from the main content sections. It uses a predefined key mapping (`KEY_MAPPING`) to transform Spanish Markdown headers/keys into desired English or standardized JSON keys. Specific handling is applied for list-like sections (e.g., "Redes Sociales", "Cursos", "Propuestas") and comma-separated tags to structure them appropriately in JSON.
    * **Output:** JSON files, one for each Markdown file, saved in a `jdata/` directory. This format is specifically prepared for the final loading step into the RAG system.

5.  **`s5loadrag.py` (Load JSON to RAG System - Open WebUI):**
    * **Input:** The JSON files from the `jdata/` directory.
    * **Process:** This script interacts with an Open WebUI instance to load the candidate data into a specified Knowledge Base Collection.
        * It first uploads each JSON file to the Open WebUI files API (`/api/v1/files/`).
        * If the upload is successful, it then adds the uploaded file (using its returned ID) to a pre-configured Knowledge Collection (`KNOWLEDGE_COLLECTION_ID`) via the `/api/v1/knowledge/{id}/file/add` endpoint.
    * **Output:** The candidate data (as JSON files) is uploaded and integrated into the specified Open WebUI Knowledge Collection, making it available for querying through the RAG system.

This pipeline ensures that candidate data is progressively refined, enriched with AI-generated tags and descriptions, and structured correctly for both the Candidate Assistant's direct Markdown consumption and for loading into a more general RAG system like Open WebUI.

## Setup and Installation

### Prerequisites

* Docker
* Docker Compose

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Prepare Candidate Data:**
    * Create the `mdata` directory in the project root if it doesn't exist:
        ```bash
        mkdir mdata
        ```
    * Add your candidate markdown files to the `mdata/` directory.
    * **Naming Convention:** Files should end with `.md`. The service expects filenames potentially ending with an underscore and numbers (e.g., `FirstName_LastName_YYYY.md` or `FirstName_LastName.md`). These trailing numbers will be removed for display purposes.

3.  **Configure Environment Variables:**
    * Copy the example environment file (if one is provided) or create a new file named `.env` in the project root.
        ```bash
        # Example: cp .env.example .env
        touch .env # If no example exists
        ```
    * Edit the `.env` file and fill in the required values:

        ```dotenv
        # Flask settings
        FLASK_APP=backend.app
        FLASK_ENV=development # or production
        SECRET_KEY=your_very_secret_random_key_here # Generate a strong random key

        # LLM API Settings (REQUIRED)
        # Ensure this URL is accessible FROM WITHIN the Docker container
        LLM_API_URL=http://<your-llm-host>:<port>/v1/chat/completions # e.g., [http://host.docker.internal:8080/v1/chat/completions](http://host.docker.internal:8080/v1/chat/completions) or http://llm-service-name:8080/...
        LLM_API_TOKEN=YOUR_LLM_API_KEY_HERE # Your API Key for the LLM service
        LLM_MODEL=your-llm-model-id # e.g., ollama/llama3, granite3.1-dense:8b

        # Logging settings
        LOG_LEVEL=INFO # DEBUG, INFO, WARNING, ERROR, CRITICAL

        # Data folder (Internal container path, should match docker-compose volume target)
        MDATA_FOLDER=/app/mdata

        # Context Prompt Template (Customize how context is presented to the LLM)
        CONTEXT_PROMPT_TEMPLATE="Here is the available information about the candidate '{candidate_name}'. Please use only this information to answer my following questions about them. If the answer is not present in this information, state that.\n\n--- Candidate Information Start ---\n{markdown_content}\n--- Candidate Information End ---\n\nNow, I will ask my questions."
        ```
    * **Important:**
        * Generate a secure `SECRET_KEY`.
        * Ensure the `LLM_API_URL` is correctly set based on where your LLM service (e.g., Open WebUI) is running relative to the Docker container. If it's on your host machine, `http://host.docker.internal:<port>/...` (Docker Desktop) or your host's IP on the Docker network might be needed. If it's another service in the `docker-compose.yml`, use the service name.
        * The `MDATA_FOLDER` should typically be `/app/mdata` to match the target path of the volume mount defined in `docker-compose.yml`.

4.  **Build and Run with Docker Compose:**
    * Open a terminal in the project root directory.
    * Run the following command:
        ```bash
        docker-compose up --build
        ```
    * To run in detached mode (in the background):
        ```bash
        docker-compose up --build -d
        ```

## Usage

1.  Once the containers are running, open your web browser and navigate to `http://localhost:5000` (or the host port you mapped in `docker-compose.yml` if changed).
2.  **Select Candidate:** Use the search bar in the top-left panel to filter candidates or browse the list. Click on a candidate name.
3.  **View Details:** The markdown content for the selected candidate will load in the top-right panel.
4.  **Chat:** Use the chat input box in the bottom-right panel to ask questions about the currently selected candidate. The LLM's responses will appear above. Token usage stats will display below the input box after each response.
5.  **Switch Conversations:**
    * Clicking a different candidate in the top-left list starts a new conversation or loads the existing one for that candidate.
    * The bottom-left panel lists all candidates you have started conversations with in this session. Clicking a name there will switch back to that specific conversation, restoring the chat history.

## Troubleshooting

* **Cannot Connect to LLM API:** Verify the `LLM_API_URL` in `.env` is correct and accessible *from within the `app` Docker container*. Check firewall rules. Use `docker-compose logs app -f` to see backend errors.
* **Markdown Not Loading / Candidate Errors:** Check backend logs (`docker-compose logs app -f`) for file path errors. Ensure the `mdata` volume is mounted correctly in `docker-compose.yml` and the `MDATA_FOLDER` in `.env` points to the correct *internal* container path (`/app/mdata`). Verify markdown files exist and have correct permissions. Check the browser console (F12) for JavaScript errors.
* **Authentication Error:** Check if `LLM_API_TOKEN` in `.env` is correct.
* **UI Issues / Colors Wrong:** Clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R) to ensure the latest CSS is loaded. Inspect elements using browser developer tools to check applied styles.
