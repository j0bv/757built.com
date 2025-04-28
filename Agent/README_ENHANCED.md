# 757 Document Analysis & IPFS Storage System

This system uses Microsoft's Phi-3 model to analyze government research documents, patents, and construction development data from Southeastern Virginia (757 area code region). It extracts structured information, creates a graph neural network of relationships, and stores documents on IPFS.

## System Components

1. **Phi-3 Quantized Model Integration**: Uses a lightweight quantized version of Microsoft's Phi-3 model for efficient document analysis on CPU.

2. **Document Analysis**: Extracts:
   - Geographic coordinates and locations
   - Funding details (amounts, sources, grant numbers)
   - Key entities (people, organizations, companies)
   - Project details (timelines, status, summaries)
   - Relationship mapping between entities

3. **IPFS Integration**: Documents are hashed and stored on IPFS for permanent, decentralized storage.

4. **Graph Database**: Creates a knowledge graph connecting all entities, locations, and projects.

5. **GeoJSON Output**: Location data is formatted as GeoJSON for easy mapping.

## Installation on root@server1

### Prerequisites

1. Python 3.7+
2. IPFS daemon
3. llama.cpp (for running the quantized model)

### Setup Steps

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install IPFS**:
   ```bash
   # Download and install IPFS
   wget https://dist.ipfs.io/go-ipfs/v0.14.0/go-ipfs_v0.14.0_linux-amd64.tar.gz
   tar -xvzf go-ipfs_v0.14.0_linux-amd64.tar.gz
   cd go-ipfs
   bash install.sh
   
   # Initialize IPFS
   ipfs init
   
   # Configure IPFS daemon to start on boot (optional)
   cp phi3-document-processor.service /etc/systemd/system/
   systemctl daemon-reload
   systemctl enable ipfs
   ```

3. **Set Up llama.cpp for Phi-3**:
   ```bash
   # Clone llama.cpp repository
   git clone https://github.com/ggerganov/llama.cpp.git
   cd llama.cpp
   
   # Build
   make
   
   # Download the quantized Phi-3 model
   # You'll need to download the model from HuggingFace:
   # https://huggingface.co/microsoft/phi-3/tree/main
   # and then convert/quantize it using llama.cpp's tools
   ```

4. **Configure Environment Variables**:
   - Create a `.env` file with your API keys and endpoints:
   ```
   WEB_API_ENDPOINT=https://server250.web-hosting.com/api/ipfs_hashes.php
   API_KEY=your_api_key_here
   ```

5. **Set Up Systemd Service**:
   ```bash
   cp phi3-document-processor.service /etc/systemd/system/
   systemctl daemon-reload
   systemctl enable phi3-document-processor
   systemctl start phi3-document-processor
   ```

## Usage

### Running the Document Processor

```bash
python enhanced_document_processor.py --model-path /path/to/phi3-q3_k_l.gguf --llama-path /path/to/llama.cpp/main
```

### Processing a Single Document

```bash
python enhanced_document_processor.py --model-path /path/to/phi3-q3_k_l.gguf --llama-path /path/to/llama.cpp/main --single-file /path/to/document.pdf
```

### Data Flow

1. Documents are placed in the `data/` directory
2. The system monitors this directory for new files
3. When a new document is found:
   - Text is extracted and analyzed by Phi-3
   - The document is hashed to IPFS
   - Structured information is stored in both local JSON and sent to the web API
   - The knowledge graph is updated

## Output

### Document Analysis (data/analysis/)

Each document analysis contains:
- Document type classification
- Project summary
- Geographic locations and coordinates
- Funding information
- Entity extraction (people, organizations, companies)
- Relationship mapping

### Graph Data (data/graph_data.json)

Contains a structured graph with:
- Nodes (people, organizations, companies, projects, locations)
- Edges (relationships between nodes)
- Properties for each node and edge

### IPFS Hashes (data/ipfs_hashes.json)

Tracks all documents with:
- IPFS hash
- Document name
- Timestamp
- Analysis summary

## Integration with Website (ybqiflhd@server250)

The system is designed to integrate with the 757built.com website hosted on server250 by:
- Sending structured data via API
- Including GeoJSON for map visualization
- Providing IPFS hashes for permanent document access

## Monitoring

Check the status of the service:
```bash
systemctl status phi3-document-processor
```

View logs:
```bash
journalctl -u phi3-document-processor -f
```

## Performance Considerations

- The quantized Phi-3 model (q3_k_l) balances performance and accuracy
- Set `--threads` based on your CPU cores
- For larger documents, consider increasing `--ctx-size`
