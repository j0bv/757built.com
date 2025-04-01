Hello, this is my capstone project for Broadcast Journalism. 

Updates on 757built.com
# Hampton Roads Technology Development Map

An interactive map visualization of technology and development initiatives in the Hampton Roads region of Virginia, using Leaflet.js with government data collection and AI-powered analysis.

## Features
- Interactive map displaying all major cities and localities in the Hampton Roads region
- Primary source document collection from government sources and public APIs
- AI-powered analysis of development projects and official documents
- Technology initiative tracking across the region
- Decentralized data storage with OrbitDB
- Responsive design for desktop and mobile devices

## System Architecture

### Data Layer
- **OrbitDB**: Decentralized, peer-to-peer database built on IPFS for storing and managing collected data
- **Data Sources**: Government APIs, planning documents, and public records from Hampton Roads jurisdictions
- **Document Storage**: Structure for maintaining and linking to primary source documents

### Collection Layer
- **Sourcing Module**: Comprehensive data collection system with web scraping and API integration
- **AI Analysis**: Document analysis using both Ollama (local) and OpenAI for extracting structured data
- **Primary Documents**: Focus on official government records, permits, planning documents, and economic reports

### Presentation Layer
- **Leaflet.js Map**: Interactive visualization of Hampton Roads region
- **City/County Boundaries**: Administrative boundaries from ArcGIS services
- **Interactive Elements**: Hover effects, popups, and data visualization components

## Technologies Used
- **Frontend**: HTML5, CSS3, JavaScript
- **Maps**: Leaflet.js with custom style layers
- **Data Collection**: 
  - Playwright (headless browser automation)
  - Axios (HTTP requests)
  - Cheerio (HTML parsing)
- **AI Integration**:
  - Ollama (local AI models)
  - OpenAI API (cloud-based models)
- **Storage**: 
  - OrbitDB (decentralized database)
  - IPFS (InterPlanetary File System)

## Data Sources
- Virginia Beach Open Data Portal
- Norfolk Development Services
- Hampton Roads Planning District Commission
- Virginia Innovation Partnership Corporation
- Hampton Roads Economic Development Alliance
- Official government planning and zoning documents

## Setup and Installation

### Prerequisites
- Node.js and npm
- Ollama (for local AI processing)
- OpenAI API key (optional)

### Installation
```bash
# Install dependencies
npm install

# Run the local development server
npm start
```

### Configuration
To configure AI providers for document analysis:

```javascript
// Use Ollama (default)
const primaryDocs = await collectHamptonRoadsPrimaryDocuments();

// Use OpenAI
const primaryDocs = await collectHamptonRoadsPrimaryDocuments({
  aiProvider: 'openai',
  openaiApiKey: 'your-api-key-here'
});
```

## Future Enhancements
- Time-based visualization of development patterns
- Machine learning model for predicting technology growth areas
- User contribution system for verified local data
- Integration with real-time economic indicators

## License
[MIT License](LICENSE)