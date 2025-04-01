// heatmap-bundle.js
// This file renders the React ContributionHeatmap component in the browser
"use strict";

// Sample data generation function - in a real application, you would fetch this from your API
const generateDummyData = () => {
  const data = [];
  const today = new Date();
  
  for (let i = 364; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    data.push({
      date: date.toISOString().split('T')[0],
      count: Math.floor(Math.random() * 10)
    });
  }
  
  return data;
};

// Helper function to determine color based on contribution count
const getContributionColor = (count) => {
  if (count === 0) return 'bg-gray-100';
  if (count <= 3) return 'bg-green-100';
  if (count <= 6) return 'bg-green-300';
  if (count <= 9) return 'bg-green-500';
  return 'bg-green-700';
};

// The contribution heatmap component
const ContributionHeatmap = () => {
  const contributions = generateDummyData();
  const weeks = [];
  
  for (let i = 0; i < contributions.length; i += 7) {
    weeks.push(contributions.slice(i, i + 7));
  }

  return React.createElement(
    'div', 
    { className: 'bg-[#2b3b80] text-white p-4 shadow-md fixed top-0 left-0 right-0 z-10' },
    React.createElement(
      'div', 
      { className: 'container mx-auto' },
      React.createElement(
        'div', 
        { className: 'flex justify-between items-center mb-3' },
        React.createElement('h1', { className: 'text-xl font-semibold' }, 'Hampton Roads Development Activity')
      ),
      React.createElement(
        'div', 
        { className: 'p-4 bg-opacity-10 bg-white rounded' },
        React.createElement('h2', { className: 'text-xl font-semibold mb-4' }, 'Contribution Activity'),
        React.createElement(
          'div', 
          { className: 'flex gap-1 overflow-x-auto pb-2' },
          weeks.map((week, weekIndex) => 
            React.createElement(
              'div', 
              { key: weekIndex, className: 'flex flex-col gap-1' },
              week.map((day, dayIndex) => 
                React.createElement('div', {
                  key: `${weekIndex}-${dayIndex}`,
                  className: `w-3 h-3 rounded-sm ${getContributionColor(day.count)}`,
                  title: `${day.count} contributions on ${day.date}`
                })
              )
            )
          )
        ),
        React.createElement(
          'div', 
          { className: 'flex items-center gap-2 mt-4 text-sm text-white' },
          React.createElement('span', {}, 'Less'),
          React.createElement(
            'div', 
            { className: 'flex gap-1' },
            React.createElement('div', { className: 'w-3 h-3 rounded-sm bg-gray-100' }),
            React.createElement('div', { className: 'w-3 h-3 rounded-sm bg-green-100' }),
            React.createElement('div', { className: 'w-3 h-3 rounded-sm bg-green-300' }),
            React.createElement('div', { className: 'w-3 h-3 rounded-sm bg-green-500' }),
            React.createElement('div', { className: 'w-3 h-3 rounded-sm bg-green-700' })
          ),
          React.createElement('span', {}, 'More')
        )
      )
    )
  );
};

// Render the heatmap component
document.addEventListener('DOMContentLoaded', () => {
  const root = document.getElementById('heatmap-root');
  if (root) {
    try {
      // For React 18
      if (ReactDOM.createRoot) {
        const reactRoot = ReactDOM.createRoot(root);
        reactRoot.render(React.createElement(ContributionHeatmap));
      } else {
        // For older React versions
        ReactDOM.render(React.createElement(ContributionHeatmap), root);
      }
      console.log("React component rendered successfully");
    } catch (e) {
      console.error("Error rendering React component:", e);
      // Fallback to basic HTML if React fails
      root.innerHTML = `
        <div class="bg-[#2b3b80] text-white p-4 shadow-md fixed top-0 left-0 right-0 z-10">
          <div class="container mx-auto">
            <h1 class="text-xl font-semibold">Hampton Roads Development Activity</h1>
            <p>Error loading heatmap component</p>
          </div>
        </div>
      `;
    }
  } else {
    console.error("Could not find heatmap-root element");
  }
});
