// Calendar Heatmap implementation inspired by StretchCalendarHeatmap React component
document.addEventListener('DOMContentLoaded', function() {
    // Configuration elements
    const currentYearEl = document.getElementById('currentYear');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');
    
    // Create popup element for contributions
    const popup = document.createElement('div');
    popup.className = 'contribution-popup';
    popup.style.display = 'none';
    document.body.appendChild(popup);
    
    // Set initial year to current year
    let currentYear = new Date().getFullYear();
    currentYearEl.textContent = currentYear;
    
    // Sample data - in a real app, this would come from an API
    const sampleData = {
        2023: {
            total: 12,
            contributions: [
                { date: "2023-01-05", count: 1 },
                { date: "2023-02-15", count: 2 },
                { date: "2023-04-10", count: 3 },
                { date: "2023-06-22", count: 1 },
                { date: "2023-08-30", count: 2 },
                { date: "2023-09-15", count: 1 },
                { date: "2023-10-12", count: 3 },
                { date: "2023-11-12", count: 3 },
            ],
        },
        2024: {
            total: 8,
            contributions: [
                { date: "2024-01-20", count: 2 },
                { date: "2024-03-15", count: 1 },
                { date: "2024-05-10", count: 3 },
                { date: "2024-07-05", count: 2 },
                { date: "2024-08-12", count: 1 },
                { date: "2024-10-25", count: 2 },
                { date: "2024-12-01", count: 3 },
            ],
        },
        2025: {
            total: 10,
            contributions: [
                { date: "2025-01-15", count: 1 },
                { date: "2025-03-10", count: 1 },
                { date: "2025-03-27", count: 3 },
                { date: "2025-05-05", count: 1 },
                { date: "2025-07-20", count: 2 },
                { date: "2025-08-15", count: 1 },
                { date: "2025-10-10", count: 3 },
                { date: "2025-11-25", count: 2 },
                { date: "2025-12-24", count: 1 },
            ],
        },
        2030: {
            total: 5,
            contributions: [
                { date: "2030-01-10", count: 1 },
                { date: "2030-02-20", count: 2 },
                { date: "2030-03-15", count: 1 },
                { date: "2030-04-05", count: 3 },
                { date: "2030-05-12", count: 2 },
            ],
        }
    };
    
    // Helper function to convert sampleData to Cal-Heatmap format
    function convertToCalHeatmapFormat(year) {
        if (!sampleData[year]) return [];
        
        return sampleData[year].contributions.map(item => ({
            date: item.date,
            count: item.count
        }));
    }
    
    // Get day suffix (st, nd, rd, th)
    function getDaySuffix(day) {
        if (day > 3 && day < 21) return "th";
        switch (day % 10) {
            case 1: return "st";
            case 2: return "nd";
            case 3: return "rd";
            default: return "th";
        }
    }
    
    // Initialize the calendar
    const cal = new CalHeatmap();
    
    // Function to update the calendar
    function updateCalendar() {
        // Get data for the current year
        const data = convertToCalHeatmapFormat(currentYear);
        
        // Paint the calendar with options
        cal.paint({
            itemSelector: '#cal-heatmap',
            domain: {
                type: 'month',
                gutter: 0, // Reduced gutter to make months appear continuous
                padding: [15, 0, 0, 0]
            },
            subDomain: {
                type: 'day',
                radius: 1,
                width: 10, // Smaller width for tighter layout
                height: 10, // Smaller height for tighter layout
                gutter: 2 // Small gutter between days
            },
            date: {
                start: new Date(currentYear, 0, 1),
                highlight: 'now'
            },
            range: 12,
            scale: {
                color: {
                    range: ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353', 
                           '#4ade80', '#60d394', '#88d498', '#bfd96c', '#ffe26a'], // Vibrant color scheme
                    type: 'threshold',
                    domain: [1, 2, 3, 5, 7] // More gradual color distribution
                }
            },
            data: {
                source: data,
                type: 'json',
                x: 'date',
                y: 'count',
                groupY: 'sum'
            },
            // Display tooltip on hover
            tooltip: {
                text: function(date, value, dayjsDate) {
                    if (!value || value === 0) {
                        return `No contributions on ${dayjsDate.format('MMMM D, YYYY')}`;
                    }
                    return `${value} contribution${value !== 1 ? 's' : ''} on ${dayjsDate.format('MMMM D, YYYY')}`;
                }
            }
        });
    }
    
    // Initial calendar render
    updateCalendar();
    
    // Add click event to show contribution popup
    document.querySelector('#cal-heatmap').addEventListener('click', function(e) {
        // Find the clicked cell
        const cell = e.target.closest('.ch-subdomain-bg');
        if (!cell) return;
        
        // Get the date from the cell
        const date = cell.getAttribute('data-date');
        if (!date) return;
        
        // Parse the date
        const dateObj = new Date(date);
        const day = dateObj.getDate();
        const month = dateObj.toLocaleDateString('en-US', { month: 'long' });
        
        // Get the contribution count
        const dataDate = dateObj.toISOString().split('T')[0];
        let count = 0;
        
        // Find the contribution in the yearly data
        const yearData = sampleData[currentYear];
        if (yearData) {
            const contribution = yearData.contributions.find(c => c.date === dataDate);
            if (contribution) count = contribution.count;
        }
        
        // Update popup content to match React component style
        popup.innerHTML = `
            <div>${count} contribution${count !== 1 ? 's' : ''} on ${month} ${day}${getDaySuffix(day)}.</div>
        `;
        
        // Position popup near the clicked cell
        const rect = cell.getBoundingClientRect();
        popup.style.left = `${rect.left + window.scrollX}px`;
        popup.style.top = `${rect.top + window.scrollY - 40}px`;
        
        // Show popup
        popup.style.display = 'block';
        
        // Hide popup after 3 seconds
        setTimeout(() => {
            popup.style.display = 'none';
        }, 3000);
    });
    
    // Event listeners for navigation
    prevYearBtn.addEventListener('click', function() {
        currentYear--;
        currentYearEl.textContent = currentYear;
        updateCalendar();
    });
    
    nextYearBtn.addEventListener('click', function() {
        currentYear++;
        currentYearEl.textContent = currentYear;
        updateCalendar();
    });
});// Calendar Heatmap implementation for Hampton Roads Development Activity
document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const calendarEl = document.getElementById('calendar-heatmap');
    const currentYearEl = document.getElementById('currentYear');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');
    
    // Set initial year to current year
    let currentYear = new Date().getFullYear();
    currentYearEl.textContent = currentYear;
    
    // Sample data - will be replaced with actual data from backend
    // Format: { date: 'YYYY-MM-DD', count: Number, locality: String }
    const sampleData = generateSampleData();
    
    // Render the calendar
    renderCalendar(currentYear);
    
    // Event listeners for navigation
    prevYearBtn.addEventListener('click', function() {
        currentYear--;
        currentYearEl.textContent = currentYear;
        renderCalendar(currentYear);
    });
    
    nextYearBtn.addEventListener('click', function() {
        currentYear++;
        currentYearEl.textContent = currentYear;
        renderCalendar(currentYear);
    });
    
    // Function to render the calendar heatmap
    function renderCalendar(year) {
        // Clear existing calendar
        calendarEl.innerHTML = '';
        
        // Get the first day of the year
        const firstDay = new Date(year, 0, 1);
        const firstDayOfWeek = firstDay.getDay(); // 0 (Sunday) to 6 (Saturday)
        
        // Create month labels
        const monthsRow = document.createElement('div');
        monthsRow.className = 'col-span-53 grid grid-cols-53 text-xs mb-1';
        calendarEl.appendChild(monthsRow);
        
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        let currentMonth = 0;
        let monthColSpan = 0;
        
        // Calculate days in each month for the given year
        for (let month = 0; month < 12; month++) {
            const daysInMonth = new Date(year, month + 1, 0).getDate();
            const firstDayOfMonth = new Date(year, month, 1).getDay();
            
            // Calculate weeks in this month
            let weeksInMonth = Math.ceil((daysInMonth + firstDayOfMonth) / 7);
            
            // Add month label
            const monthLabel = document.createElement('div');
            monthLabel.className = `col-span-${weeksInMonth} text-center`;
            monthLabel.textContent = months[month];
            monthsRow.appendChild(monthLabel);
        }
        
        // Create day of week labels
        const daysRow = document.createElement('div');
        daysRow.className = 'grid grid-cols-1 gap-1 text-xs text-right pr-2';
        calendarEl.appendChild(daysRow);
        
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        for (let i = 0; i < 7; i++) {
            if (i % 2 === 0) { // Only show every other day to save space
                const dayLabel = document.createElement('div');
                dayLabel.className = 'h-4';
                dayLabel.textContent = days[i];
                daysRow.appendChild(dayLabel);
            } else {
                const emptyLabel = document.createElement('div');
                emptyLabel.className = 'h-4';
                daysRow.appendChild(emptyLabel);
            }
        }
        
        // Create calendar cells
        const weeksContainer = document.createElement('div');
        weeksContainer.className = 'grid grid-cols-53 gap-1';
        calendarEl.appendChild(weeksContainer);
        
        // Create 7 rows (days of week) with 53 columns (weeks in year)
        for (let day = 0; day < 7; day++) {
            const dayRow = document.createElement('div');
            dayRow.className = 'col-span-53 grid grid-cols-53 gap-1';
            weeksContainer.appendChild(dayRow);
            
            for (let week = 0; week < 53; week++) {
                // Calculate the date for this cell
                const date = new Date(year, 0, 1);
                date.setDate(1 + week * 7 + day - firstDayOfWeek);
                
                // Skip if date is not in the current year
                if (date.getFullYear() !== year) {
                    const emptyCell = document.createElement('div');
                    emptyCell.className = 'w-3 h-3 opacity-0';
                    dayRow.appendChild(emptyCell);
                    continue;
                }
                
                // Format date as YYYY-MM-DD
                const formattedDate = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
                
                // Find activity count for this date
                const dateData = sampleData.filter(d => d.date === formattedDate);
                const count = dateData.length;
                
                // Determine cell color based on count
                let cellColor = '#ebedf0'; // Default: no activity
                if (count > 0) cellColor = '#9be9a8';
                if (count > 2) cellColor = '#40c463';
                if (count > 5) cellColor = '#30a14e';
                if (count > 10) cellColor = '#216e39';
                
                // Create cell
                const cell = document.createElement('div');
                cell.className = 'w-3 h-3 rounded-sm cursor-pointer';
                cell.style.backgroundColor = cellColor;
                
                // Add tooltip with activity information
                const tooltip = document.createElement('div');
                tooltip.className = 'absolute hidden group-hover:block bg-gray-800 text-white p-2 rounded-md text-xs whitespace-nowrap z-50 -mt-10 -ml-2';
                
                if (count > 0) {
                    const projects = dateData.map(d => d.locality).join(', ');
                    cell.title = `${count} activities on ${formattedDate}\nLocalities: ${projects}`;
                } else {
                    cell.title = `No activity on ${formattedDate}`;
                }
                
                const cellContainer = document.createElement('div');
                cellContainer.className = 'relative group';
                cellContainer.appendChild(cell);
                dayRow.appendChild(cellContainer);
            }
        }
    }
    
    // Generate sample data for testing
    function generateSampleData() {
        const localities = [
            "NORFOLK", "VIRGINIA BEACH", "CHESAPEAKE", "PORTSMOUTH", 
            "SUFFOLK", "HAMPTON", "NEWPORT NEWS", "WILLIAMSBURG",
            "JAMES CITY", "GLOUCESTER", "YORK", "POQUOSON",
            "ISLE OF WIGHT", "SURRY", "SOUTHAMPTON", "SMITHFIELD"
        ];
        
        const data = [];
        const currentYear = new Date().getFullYear();
        
        // Generate random data for the last year
        for (let i = 0; i < 300; i++) {
            const randomMonth = Math.floor(Math.random() * 12);
            const randomDay = Math.floor(Math.random() * 28) + 1; // Avoid day 29-31 issues
            const randomLocality = localities[Math.floor(Math.random() * localities.length)];
            
            const date = `${currentYear}-${String(randomMonth + 1).padStart(2, '0')}-${String(randomDay).padStart(2, '0')}`;
            
            data.push({
                date: date,
                count: 1,
                locality: randomLocality
            });
        }
        
        return data;
    }
});

// Function to update the calendar with real data from backend
// This will be called when you implement your backend
function updateCalendarWithRealData(data) {
    // Clear existing calendar
    const calendarEl = document.getElementById('calendar-heatmap');
    calendarEl.innerHTML = '';
    
    // Re-render with real data
    renderCalendar(new Date().getFullYear(), data);
}// Calendar Heatmap implementation for Hampton Roads Development Activity
document.addEventListener('DOMContentLoaded', function() {
    // Configuration
    const calendarEl = document.getElementById('calendar-heatmap');
    const currentYearEl = document.getElementById('currentYear');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');
    
    // Set initial year to current year
    let currentYear = new Date().getFullYear();
    currentYearEl.textContent = currentYear;
    
    // Sample data - will be replaced with actual data from backend
    // Format: { date: 'YYYY-MM-DD', count: Number, locality: String }
    const sampleData = generateSampleData();
    
    // Render the calendar
    renderCalendar(currentYear, sampleData);
    
    // Event listeners for navigation
    prevYearBtn.addEventListener('click', function() {
        currentYear--;
        currentYearEl.textContent = currentYear;
        renderCalendar(currentYear, sampleData);
    });
    
    nextYearBtn.addEventListener('click', function() {
        currentYear++;
        currentYearEl.textContent = currentYear;
        renderCalendar(currentYear, sampleData);
    });
    
    // Function to render the calendar heatmap
    function renderCalendar(year, data) {
        // Clear existing calendar
        calendarEl.innerHTML = '';
        
        // Get the first day of the year
        const firstDay = new Date(year, 0, 1);
        const firstDayOfWeek = firstDay.getDay(); // 0 (Sunday) to 6 (Saturday)
        
        // Set up grid template columns based on weeks in the year
        const weeksInYear = getWeeksInYear(year);
        calendarEl.style.gridTemplateColumns = `repeat(${weeksInYear}, minmax(10px, 1fr))`;
        
        // Create calendar cells in a grid (7 days per week)
        for (let day = 0; day < 7; day++) {
            const dayRow = document.createElement('div');
            dayRow.className = 'flex gap-[2px]';
            calendarEl.appendChild(dayRow);
            
            // Calculate date offset based on first day of year
            let dayOffset = day - firstDayOfWeek;
            if (dayOffset < 0) dayOffset += 7;
            
            for (let week = 0; week < weeksInYear; week++) {
                // Calculate the date for this cell
                const dayNum = week * 7 + dayOffset;
                const date = new Date(year, 0, 1);
                date.setDate(1 + dayNum);
                
                // Skip if date is outside the current year
                if (date.getFullYear() !== year) {
                    const emptyCell = document.createElement('div');
                    emptyCell.className = 'w-[10px] h-[10px] opacity-0';
                    dayRow.appendChild(emptyCell);
                    continue;
                }
                
                // Format date as YYYY-MM-DD
                const formattedDate = formatDate(date);
                
                // Find activity count for this date
                const activitiesOnDate = data.filter(d => d.date === formattedDate);
                const count = activitiesOnDate.length;
                
                // Determine intensity level (0-4) based on count
                let intensityLevel = 0;
                if (count > 0) intensityLevel = 1;
                if (count > 2) intensityLevel = 2;
                if (count > 5) intensityLevel = 3;
                if (count > 10) intensityLevel = 4;
                
                // Create cell
                const cell = document.createElement('div');
                cell.className = `w-[10px] h-[10px] rounded-sm intensity-${intensityLevel} hover:transform hover:scale-150 transition-all`;
                
                // Add tooltip with activity information
                if (count > 0) {
                    const tooltipContent = `
                        ${count} activit${count === 1 ? 'y' : 'ies'} on ${formatDateForDisplay(date)}
                        Localities: ${[...new Set(activitiesOnDate.map(d => d.locality))].join(', ')}
                    `;
                    cell.setAttribute('title', tooltipContent);
                    cell.classList.add('cursor-pointer');
                } else {
                    cell.setAttribute('title', `No activity on ${formatDateForDisplay(date)}`);
                }
                
                dayRow.appendChild(cell);
            }
        }
    }
    
    // Helper function to get weeks in a year
    function getWeeksInYear(year) {
        const firstDayOfYear = new Date(year, 0, 1);
        const lastDayOfYear = new Date(year, 11, 31);
        
        // Calculate days in the year
        const daysInYear = (lastDayOfYear - firstDayOfYear) / (1000 * 60 * 60 * 24) + 1;
        
        // Add the day of week of the first day of the year (0-6)
        const offset = firstDayOfYear.getDay();
        
        // Calculate weeks
        return Math.ceil((daysInYear + offset) / 7);
    }
    
    // Helper function to format date as YYYY-MM-DD
    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    // Helper function to format date for display
    function formatDateForDisplay(date) {
        const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }
    
    // Generate sample data for testing
    function generateSampleData() {
        const localities = [
            "NORFOLK", "VIRGINIA BEACH", "CHESAPEAKE", "PORTSMOUTH", 
            "SUFFOLK", "HAMPTON", "NEWPORT NEWS", "WILLIAMSBURG",
            "JAMES CITY", "GLOUCESTER", "YORK", "POQUOSON",
            "ISLE OF WIGHT", "SURRY", "SOUTHAMPTON", "SMITHFIELD"
        ];
        
        const data = [];
        const currentYear = new Date().getFullYear();
        
        // Create a biased distribution with more events in recent months
        for (let i = 0; i < 500; i++) {
            // Bias toward recent months (higher probability for recent months)
            const randomBias = Math.pow(Math.random(), 1.5); // Power curve for bias
            const randomMonth = Math.floor(randomBias * 12);
            const randomDay = Math.floor(Math.random() * 28) + 1; // Avoid day 29-31 issues
            
            // Choose a locality, with Seven Cities appearing more frequently
            let randomLocality;
            const sevenCities = ["CHESAPEAKE", "HAMPTON", "NEWPORT NEWS", "NORFOLK", 
                               "PORTSMOUTH", "SUFFOLK", "VIRGINIA BEACH"];
            
            if (Math.random() < 0.7) { // 70% chance of selecting a Seven City
                randomLocality = sevenCities[Math.floor(Math.random() * sevenCities.length)];
            } else {
                randomLocality = localities[Math.floor(Math.random() * localities.length)];
            }
            
            const date = `${currentYear}-${String(randomMonth + 1).padStart(2, '0')}-${String(randomDay).padStart(2, '0')}`;
            
            data.push({
                date: date,
                count: 1,
                locality: randomLocality
            });
        }
        
        return data;
    }
});

// Function for future backend integration
function updateCalendarWithRealData(data) {
    const currentYear = document.getElementById('currentYear').textContent;
    renderCalendar(parseInt(currentYear), data);
}// Cal-Heatmap implementation for Hampton Roads Development Activity
document.addEventListener('DOMContentLoaded', function() {
    // Configuration elements
    const currentYearEl = document.getElementById('currentYear');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');
    
    // Set initial year to current year
    let currentYear = new Date().getFullYear();
    currentYearEl.textContent = currentYear;
    
    // Generate sample data for the heatmap
    const sampleData = generateSampleData();
    
    // Initialize the calendar
    const cal = new CalHeatmap();
    
    // Paint the calendar with initial options
    cal.paint({
        itemSelector: '#cal-heatmap',
        domain: {
            type: 'month',
            gutter: 4,
            padding: [15, 0, 0, 0]
        },
        subDomain: {
            type: 'day',
            radius: 2,
            width: 12,
            height: 12,
            gutter: 2
        },
        date: {
            start: new Date(currentYear, 0, 1),
            highlight: 'now'
        },
        range: 12,
        scale: {
            color: {
                range: ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39'],
                type: 'threshold',
                domain: [1, 3, 6, 10]
            }
        },
        data: {
            source: sampleData,
            type: 'json',
            x: 'date',
            y: 'count',
            groupY: 'sum'
        },
        // Display tooltip on hover
        tooltip: {
            text: function(date, value, dayjsDate) {
                if (!value || value === 0) {
                    return `No activity on ${dayjsDate.format('MMMM D, YYYY')}`;
                }
                
                // Find all localities with activities on this date
                const dateStr = dayjsDate.format('YYYY-MM-DD');
                const activitiesOnDate = sampleData.filter(d => d.date === dateStr);
                const localities = [...new Set(activitiesOnDate.map(d => d.locality))];
                
                return `
                    <div class="cal-tooltip">
                        <div class="cal-tooltip-date">${dayjsDate.format('MMMM D, YYYY')}</div>
                        <div class="cal-tooltip-value">${value} development ${value === 1 ? 'activity' : 'activities'}</div>
                        <div class="cal-tooltip-localities">Localities: ${localities.join(', ')}</div>
                    </div>
                `;
            }
        }
    });
    
    // Event listeners for navigation
    prevYearBtn.addEventListener('click', function() {
        currentYear--;
        currentYearEl.textContent = currentYear;
        cal.paint({
            date: {
                start: new Date(currentYear, 0, 1)
            }
        });
    });
    
    nextYearBtn.addEventListener('click', function() {
        currentYear++;
        currentYearEl.textContent = currentYear;
        cal.paint({
            date: {
                start: new Date(currentYear, 0, 1)
            }
        });
    });
    
    // Function to format date as YYYY-MM-DD
    function formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    // Generate sample data for testing
    function generateSampleData() {
        const localities = [
            "NORFOLK", "VIRGINIA BEACH", "CHESAPEAKE", "PORTSMOUTH", 
            "SUFFOLK", "HAMPTON", "NEWPORT NEWS", "WILLIAMSBURG",
            "JAMES CITY", "GLOUCESTER", "YORK", "POQUOSON",
            "ISLE OF WIGHT", "SURRY", "SOUTHAMPTON", "SMITHFIELD"
        ];
        
        const sevenCities = [
            "CHESAPEAKE", "HAMPTON", "NEWPORT NEWS", "NORFOLK", 
            "PORTSMOUTH", "SUFFOLK", "VIRGINIA BEACH"
        ];
        
        const data = [];
        const currentYear = new Date().getFullYear();
        const startDate = new Date(currentYear, 0, 1);
        const endDate = new Date(currentYear, 11, 31);
        
        // Create a biased distribution with more events in recent months
        for (let i = 0; i < 500; i++) {
            // Bias toward recent months (higher probability for recent months)
            const randomBias = Math.pow(Math.random(), 1.5); // Power curve for bias
            
            // Create a random date between start and end
            const dayRange = (endDate - startDate) / (1000 * 60 * 60 * 24);
            const randomDay = Math.floor(randomBias * dayRange);
            const date = new Date(startDate);
            date.setDate(date.getDate() + randomDay);
            
            // Choose a locality, with Seven Cities appearing more frequently
            let randomLocality;
            if (Math.random() < 0.7) { // 70% chance of selecting a Seven City
                randomLocality = sevenCities[Math.floor(Math.random() * sevenCities.length)];
            } else {
                randomLocality = localities[Math.floor(Math.random() * localities.length)];
            }
            
            // Format the date as YYYY-MM-DD
            const formattedDate = formatDate(date);
            
            data.push({
                date: formattedDate,
                count: 1,
                locality: randomLocality
            });
        }
        
        return data;
    }
});

// Function for future backend integration
function updateCalendarWithRealData(data) {
    const cal = new CalHeatmap();
    const currentYear = parseInt(document.getElementById('currentYear').textContent);
    
    cal.paint({
        itemSelector: '#cal-heatmap',
        date: {
            start: new Date(currentYear, 0, 1)
        },
        data: {
            source: data,
            type: 'json',
            x: 'date',
            y: 'count'
        }
    });
}// Cal-Heatmap implementation for Hampton Roads Development Activity
document.addEventListener('DOMContentLoaded', function() {
    // Configuration elements
    const currentYearEl = document.getElementById('currentYear');
    const prevYearBtn = document.getElementById('prevYear');
    const nextYearBtn = document.getElementById('nextYear');
    
    // Create popup element for contributions
    const popup = document.createElement('div');
    popup.className = 'contribution-popup';
    popup.style.display = 'none';
    document.body.appendChild(popup);
    
    // Set initial year to current year
    let currentYear = new Date().getFullYear();
    currentYearEl.textContent = currentYear;
    
    // Generate sample data for the heatmap
    const sampleData = generateSampleData();
    
    // Initialize the calendar
    const cal = new CalHeatmap();
    
    // Paint the calendar with initial options
    cal.paint({
        itemSelector: '#cal-heatmap',
        domain: {
            type: 'month',
            gutter: 4,
            padding: [15, 0, 0, 0]
        },
        subDomain: {
            type: 'day',
            radius: 2,
            width: 12,
            height: 12,
            gutter: 2
        },
        date: {
            start: new Date(currentYear, 0, 1),
            highlight: 'now'
        },
        range: 12,
        scale: {
            color: {
                range: ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353'],
                type: 'threshold',
                domain: [1, 3, 6, 10]
            }
        },
        data: {
            source: sampleData,
            type: 'json',
            x: 'date',
            y: 'count',
            groupY: 'sum'
        },
        // Display tooltip on hover
        tooltip: {
            text: function(date, value, dayjsDate) {
                if (!value || value === 0) {
                    return `No contributions on ${dayjsDate.format('MMMM D, YYYY')}`;
                }
                return `${value} contribution${value !== 1 ? 's' : ''} on ${dayjsDate.format('MMMM D, YYYY')}`;
            }
        }
    });
    
    // Add click event to show contribution popup
    document.querySelector('#cal-heatmap').addEventListener('click', function(e) {
        // Find the clicked cell
        const cell = e.target.closest('.ch-subdomain-bg');
        if (!cell) return;
        
        // Get the date from the cell
        const date = cell.getAttribute('data-date');
        if (!date) return;
        
        // Find contributions for this date
        const dateObj = new Date(date);
        const formattedDate = formatDate(dateObj);
        
        // Count contributions for this date
        const dateContributions = sampleData.filter(d => d.date === formattedDate);
        const count = dateContributions.length;
        
        // Format date for