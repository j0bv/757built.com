// Main controller for 757Built Cyber Dashboard
import { initializeGlobe } from './widgets/globe.js';
import { initializeNetworkGraph } from './widgets/network.js';
import { initializeTimeline } from './widgets/timeline.js';
import { initializeProjectTable } from './widgets/projects.js';
import { loadSystemStats } from './widgets/systemStats.js';
import { setupMediaPlayer } from './widgets/mediaPlayer.js';
import { initFundingAllocation } from './widgets/funding.js';
import { initDocumentLibrary } from './widgets/documentLibrary.js';
import { attachVirtualKeyboard } from './virtualKeyboard.js';

// Accessibility features
const A11Y_SETTINGS = {
  highContrast: false,
  largeText: false,
  reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches
};

// Initialize all dashboard components
document.addEventListener('DOMContentLoaded', () => {
  console.log('757Built CyberDash initializing...');
  
  // SystemStats counter from API
  loadSystemStats();
  
  // Initialize widgets with API connections
  initializeProjectTable('/api/search');
  initializeNetworkGraph('/api/search/multi');
  initializeTimeline('/api/search');
  initializeGlobe('/api/search');
  initFundingAllocation('/api/search');
  initDocumentLibrary('/api/search');
  
  // Set up keyboard for touch devices
  if ('ontouchstart' in window) {
    attachVirtualKeyboard();
  }
  
  // Media player setup from eDEX UI
  setupMediaPlayer();
  
  // Initialize Clock widget from eDEX UI
  new Clock({
    containerId: 'mod_clock',
    timeFormat: 'h:mm:ss a',
    dateFormat: 'EEEE, MMM d, yyyy',
    showDate: true
  });
  
  // Handle accessibility settings
  setupAccessibilityControls();
  
  // Set up mediaPlayer toggle
  document.getElementById('openMediaPlayer').addEventListener('click', () => {
    document.getElementById('mediaPlayer').style.display = 'block';
  });
  
  document.getElementById('closeMediaPlayer').addEventListener('click', () => {
    document.getElementById('mediaPlayer').style.display = 'none';
  });
  
  // Load keyboard from eDEX UI
  new Keyboard({
    layout: "en-US",
    container: "keyboard"
  });
  
  console.log('757Built CyberDash initialized.');
});

// Accessibility controls 
function setupAccessibilityControls() {
  // Check system preferences
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.body.classList.add('reduced-motion');
  }
  
  // Add keyboard shortcut listener
  document.addEventListener('keydown', (e) => {
    // Alt+Shift+A toggles accessibility panel
    if (e.altKey && e.shiftKey && e.key === 'A') {
      toggleAccessibilityPanel();
    }
  });
}

function toggleAccessibilityPanel() {
  // Create panel if it doesn't exist
  if (!document.getElementById('a11y-panel')) {
    const panel = document.createElement('div');
    panel.id = 'a11y-panel';
    panel.className = 'a11y-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-labelledby', 'a11y-title');
    
    panel.innerHTML = `
      <div class="a11y-panel-header">
        <h2 id="a11y-title">Accessibility Settings</h2>
        <button class="a11y-close" aria-label="Close accessibility panel">&times;</button>
      </div>
      <div class="a11y-panel-body">
        <div class="a11y-option">
          <input type="checkbox" id="high-contrast" ${A11Y_SETTINGS.highContrast ? 'checked' : ''}>
          <label for="high-contrast">High Contrast Mode</label>
        </div>
        <div class="a11y-option">
          <input type="checkbox" id="large-text" ${A11Y_SETTINGS.largeText ? 'checked' : ''}>
          <label for="large-text">Large Text</label>
        </div>
        <div class="a11y-option">
          <input type="checkbox" id="reduced-motion" ${A11Y_SETTINGS.reducedMotion ? 'checked' : ''}>
          <label for="reduced-motion">Reduced Motion</label>
        </div>
      </div>
    `;
    
    document.body.appendChild(panel);
    
    // Set up event listeners
    panel.querySelector('.a11y-close').addEventListener('click', toggleAccessibilityPanel);
    
    panel.querySelector('#high-contrast').addEventListener('change', (e) => {
      A11Y_SETTINGS.highContrast = e.target.checked;
      applyAccessibilitySettings();
    });
    
    panel.querySelector('#large-text').addEventListener('change', (e) => {
      A11Y_SETTINGS.largeText = e.target.checked;
      applyAccessibilitySettings();
    });
    
    panel.querySelector('#reduced-motion').addEventListener('change', (e) => {
      A11Y_SETTINGS.reducedMotion = e.target.checked;
      applyAccessibilitySettings();
    });
  } else {
    const panel = document.getElementById('a11y-panel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  }
}

function applyAccessibilitySettings() {
  if (A11Y_SETTINGS.highContrast) {
    document.body.classList.add('high-contrast');
  } else {
    document.body.classList.remove('high-contrast');
  }
  
  if (A11Y_SETTINGS.largeText) {
    document.body.classList.add('large-text');
  } else {
    document.body.classList.remove('large-text');
  }
  
  if (A11Y_SETTINGS.reducedMotion) {
    document.body.classList.add('reduced-motion');
  } else {
    document.body.classList.remove('reduced-motion');
  }
  
  // Store settings in localStorage
  localStorage.setItem('a11y-settings', JSON.stringify(A11Y_SETTINGS));
}

// Load settings from localStorage on startup
function loadSavedAccessibilitySettings() {
  const savedSettings = localStorage.getItem('a11y-settings');
  if (savedSettings) {
    const settings = JSON.parse(savedSettings);
    Object.assign(A11Y_SETTINGS, settings);
    applyAccessibilitySettings();
  }
}

// Call on init
loadSavedAccessibilitySettings();
