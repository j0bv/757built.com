# 757built.com Server Architecture

This document explains the server architecture for the 757built.com platform, which consists of two servers with distinct roles.

## Server Overview

### Server 1: Web Hosting (ybqiflhd@server250.web-hosting.com)
- **Role**: Hosts the public-facing website
- **Port**: 21098
- **Content**: Open-source GitHub repository (https://github.com/j0bv/757built.com)
- **Stack**: PHP, MySQL, JavaScript, HTML/CSS

### Server 2: AI Processing Server (root@192.64.115.213)
- **Role**: Runs Microsoft's Phi-3 AI model for document processing and IPFS for decentralized storage
- **Port**: 21098
- **Content**: Crawler scripts, Phi-3 model via Ollama, IPFS node
- **Stack**: Python, Ollama, IPFS

## Communication Flow

1. **Data Collection**:
   - Server 2 periodically crawls sources for tech development information
   - Phi-3 model processes and extracts structured data from documents
   - Documents are hashed and stored on IPFS for decentralized access

2. **Data Storage**:
   - Structured data is uploaded to the MySQL database on Server 1
   - IPFS hashes are recorded for document verification
   - Document metadata is stored in a searchable format

3. **Website Access**:
   - Users access the website on Server 1
   - Interactive maps and data visualizations fetch from the MySQL database
   - Documents can be verified via IPFS hashes

## Setup Instructions

### Server 1 Setup (Web Host)

To deploy the website to Server 1:

```bash
# Run from your local machine
chmod +x deploy_web.sh
./deploy_web.sh
```

This will:
- Clone the GitHub repository to the web server
- Set up the MySQL database tables
- Configure automatic updates via cron job

### Server 2 Setup (AI Processing)

To set up the AI processing server:

```bash
# Run on Server 2
chmod +x setup_phi3_server.sh
./setup_phi3_server.sh
```

This will:
- Install Ollama and download the Phi-3 model
- Set up IPFS for document storage
- Configure the crawler scripts and database connection
- Create a service to monitor and hash new documents

## Security Considerations

- Both servers use SSH on port 21098, which is not a conflict as they are separate machines
- Database credentials are stored in .env files and not committed to GitHub
- IPFS provides content-addressable storage with cryptographic verification
- The web server API has security headers and access controls configured

## Maintenance

- Server 1 automatically pulls updates from GitHub every 6 hours
- Server 2 runs the crawler every 4 hours to collect new data
- IPFS maintains a distributed hash table of all documents
- Logs are available in standard locations on both servers

## Future Enhancements

- Implement a secure API between servers for real-time updates
- Add webhook support for triggering crawls when new sources are identified
- Enhance the Phi-3 prompt engineering for better information extraction
- Develop a user contribution system for verified local data 