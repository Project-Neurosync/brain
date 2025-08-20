# NeuroSync RAG Demo

A standalone demonstration of Retrieval Augmented Generation capabilities using Llama and ChromaDB. This demo showcases the core document ingestion, storage, and retrieval features similar to the main NeuroSync product.

## Features

- 📄 **Document Ingestion**: Upload and process PDF, DOCX, TXT, MD, and CSV files
- 🔍 **Vector Embedding**: Documents are converted to semantic vector embeddings
- 💾 **Knowledge Storage**: ChromaDB efficiently stores and indexes document embeddings
- ❓ **Natural Language Queries**: Ask questions about your documents in plain English
- 🤖 **AI-Powered Answers**: Llama model generates concise, relevant responses
- 📊 **Source Attribution**: Answers include references to source documents

## Setup Instructions

### 1. Prerequisites

- Python 3.9+ installed
- 4GB+ of RAM available for Llama model
- Sufficient disk space for document storage

### 2. Download Llama Model

Download a quantized Llama model (recommended: Llama-2-7B-Chat) from [TheBloke's Hugging Face repository](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/tree/main) and place it in a `models` directory:

```bash
mkdir -p models
# Download a quantized model (example: 4-bit quantized)
wget -O models/llama-2-7b-chat.Q4_K_M.gguf https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf
```

### 3. Install Dependencies

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run the Demo

```bash
# Set the model path (optional - default is models/llama-2-7b-chat.Q4_K_M.gguf)
export LLAMA_MODEL_PATH="models/llama-2-7b-chat.Q4_K_M.gguf"  # On Windows: set LLAMA_MODEL_PATH=models\llama-2-7b-chat.Q4_K_M.gguf

# Run the Streamlit app
streamlit run app.py
```

The application will be available at http://localhost:8501

## Usage Guide

1. **Upload Documents**: Use the sidebar file uploader to add documents
2. **Build Knowledge Index**: Click "Build Knowledge Index" after uploading files
3. **Ask Questions**: Type your question in the main input field and click "Get Answer"
4. **View History**: Previous questions and answers are stored in the query history section
5. **Reset Demo**: Use the "Reset Demo" button to clear all documents and start fresh

## System Requirements

- **Minimum**: 4GB RAM, dual-core CPU, 5GB disk space
- **Recommended**: 8GB+ RAM, quad-core CPU, SSD storage

## Troubleshooting

- If you encounter CUDA/GPU issues, the demo will automatically fall back to CPU processing
- For memory errors, try using a smaller Llama model (e.g., 7B instead of 13B)
- If documents fail to process, check file formats and encodings

## License

This demo is provided for demonstration purposes only and contains technologies under various licenses.

## About NeuroSync

This demo showcases only the basic RAG capabilities of our full NeuroSync platform. The complete product includes:

- GitHub, Jira, Slack, and Confluence integration
- Advanced code understanding and visualization
- Timeline-based knowledge management
- Team collaboration features
- ML-based importance filtering
- Project-specific knowledge contextualization

For more information, visit our website or contact our team.
