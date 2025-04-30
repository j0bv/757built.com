# Phi-3 Model Testing and IPFS Document Publishing

This repository contains tools for testing the Phi-3 model on document processing and publishing processed documents to IPFS.

## Overview

The system consists of three main components:
1. **Ingestion Framework** - Collects documents from various sources
2. **Phi-3 Document Processor** - Processes documents using the Phi-3 model
3. **IPFS Publishing** - Verifies and publishes processed documents to IPFS

## Setup & Installation

### Prerequisites

- Python 3.8+
- Redis server
- IPFS daemon running
- Phi-3 model in GGUF format

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Redis (if not already installed):
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
```

3. Ensure IPFS daemon is running:
```bash
ipfs daemon
```

## Testing Phi-3 on Server1

### Running the Test

1. Make the test script executable:
```bash
chmod +x test_phi3_server1.sh
```

2. Edit the script to set the correct path to your Phi-3 model:
```bash
# Open the file
nano test_phi3_server1.sh

# Update the PHI3_MODEL_PATH variable
PHI3_MODEL_PATH="/actual/path/to/phi3.gguf"
```

3. Run the test script:
```bash
./test_phi3_server1.sh
```

### Monitoring

- Check the processor log:
```bash
tail -f logs/processor.log
```

- Check the orchestrator log:
```bash
tail -f logs/orchestrator.log
```

- Check processed documents:
```bash
ls -la data/processed/
```

## Adding New Data Sources

The ingestion framework supports pluggable data sources. To add a new source:

1. Create a new Python file in `ingestion/plugins/`
2. Implement a class that inherits from `SourcePlugin`
3. Set a unique `name` class attribute
4. Implement the `fetch()` method that yields documents

Example:
```python
from ingestion import SourcePlugin

class MyCustomSource(SourcePlugin):
    name = "custom_source"
    
    def fetch(self):
        for document in my_data_source():
            yield {
                "id": document.id,
                "content": document.content,
                "title": document.title,
                "source": self.name,
                "timestamp": document.published_at
            }
```

## Batch Publishing to IPFS

### Verifying Documents

Before publishing to IPFS, verify that documents meet quality standards:

```bash
python -m ipfs.verify_data --dir data/processed
```

### Uploading to IPFS

Once documents are verified, upload them to IPFS:

```bash
python -m ipfs.batch_upload --dir data/processed
```

To limit the number of documents uploaded:

```bash
python -m ipfs.batch_upload --dir data/processed --limit 10
```

## Workflow

1. Start Redis server:
```bash
redis-server
```

2. Run the document processor with Phi-3 model:
```bash
python Agent/enhanced_document_processor.py --model-path /path/to/phi3.gguf --queue
```

3. Run the ingestion orchestrator:
```bash
python -m ingestion.orchestrator --out data/raw
```

4. Verify processed documents:
```bash
python -m ipfs.verify_data
```

5. Upload verified documents to IPFS:
```bash
python -m ipfs.batch_upload
```

## Troubleshooting

- **Redis Connection Error**: Ensure Redis is running with `redis-cli ping`
- **IPFS Connection Error**: Ensure IPFS daemon is running with `ipfs swarm peers`
- **Missing Documents**: Check that output directories exist and have proper permissions
- **Slow Processing**: Check CPU/memory usage and consider reducing batch size or using a smaller model variant

## License

This project is licensed under the MIT License - see the LICENSE file for details. 