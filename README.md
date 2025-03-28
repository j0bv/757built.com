# Hampton Roads Map

An interactive map of the Hampton Roads region in Virginia using Leaflet.js.

## Directory Structure
/var/www/757built.com/
├── public_html/                # Web root
│   ├── index.html              # Main map page
│   ├── css/                    # Stylesheets
│   ├── js/                     # JavaScript files
│   │   ├── map.js              # Leaflet map code
│   │   └── tech-data.js        # Technology data handling
│   ├── api/                    # API endpoints
│   │   └── technology-data.php # Data access endpoint
│   └── assets/                 # Images, icons, etc.
├── crawler/                    # Crawler code (not public)
│   ├── crawler.py              # Main crawler code
│   ├── README.md               # Documentation
│   └── requirements.txt        # Python dependencies
└── .env                        # Environment variable

## Official Government Links
- **Virginia Beach**  
  • Official site: [https://virginiabeach.gov](https://virginiabeach.gov)  
  • Public Works: [pw.virginiabeach.gov](https://pw.virginiabeach.gov)

- **Chesapeake**  
  • Official site: [cityofchesapeake.net](https://www.cityofchesapeake.net)  

- **Portsmouth**  
  • Official site: [portsmouthva.gov](https://www.portsmouthva.gov)  

- **Suffolk**  
  • Official site: [suffolkva.us](https://www.suffolkva.us)  

- **Hampton**  
  • Official site: [hampton.gov](https://hampton.gov)  
  • Public Works: [hampton.gov/4077/Public-Works](https://hampton.gov/4077/Public-Works)

- **Newport News**  
  • Official site: [newportnewsva.gov](https://www.newportnewsva.gov)  

- **Williamsburg**  
  • Official site: [williamsburgva.gov](https://www.williamsburgva.gov)  
  
- **James City County**  
  • Official site: [jamescitycountyva.gov](https://www.jamescitycountyva.gov)  
  
- **Gloucester County**  
  • Official site: [gloucesterva.gov](https://www.gloucesterva.gov)  

- **York County**  
  • Official site: [yorkcountyva.gov](https://www.yorkcountyva.gov)  

- **Poquoson**  
  • Official site: [poquosonva.gov](https://www.poquosonva.gov)  

- **Smithfield**  
  • Official site: [smithfield-va.gov](https://www.smithfield-va.gov)  

- **Isle of Wight County**  
  • Official site: [isleofwightcounty.com](https://www.isleofwightcounty.com)  

- **Surry County**  
  • Official site: [surrycountyva.gov](https://www.surrycountyva.gov)  

- **Southampton County**  
  • Official site (if available): [southamptoncountyva.gov](https://www.southamptoncountyva.gov)  

- **Franklin**  
  • Official site: [franklinva.gov](https://www.franklinva.gov)

## Features
- Displays all major cities and localities in the Hampton Roads region
- Interactive map with city markers and labels
- Responsive design

## Technologies Used
- HTML5
- CSS3
- JavaScript
- Leaflet.js
- Administrative Boundaries
https://vginmaps.vdem.virginia.gov/arcgis/rest/services/VA_Base_Layers/VA_Admin_Boundaries/FeatureServer/1/query


## Setup
1. Clone this repository
2. Open index.html in your browser

## Features
GeoJSON boundary data for more accurate city borders

## Future Improvements
- Add information popups with tech development news and key role players
- Add search functionality
- Video interviews with key role players
- Add audio and video to the map
