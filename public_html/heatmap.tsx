import React from 'react';

type ContributionDay = {
  date: string;
  count: number;
};

const generateDummyData = (): ContributionDay[] => {
  const data: ContributionDay[] = [];
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

const getContributionColor = (count: number): string => {
  if (count === 0) return 'bg-gray-100';
  if (count <= 3) return 'bg-green-100';
  if (count <= 6) return 'bg-green-300';
  if (count <= 9) return 'bg-green-500';
  return 'bg-green-700';
};

const ContributionHeatmap: React.FC = () => {
  const contributions = generateDummyData();
  const weeks = [];
  
  for (let i = 0; i < contributions.length; i += 7) {
    weeks.push(contributions.slice(i, i + 7));
  }

  return (
    <div className="p-4">
      <h2 className="text-xl font-semibold mb-4">Contribution Activity</h2>
      <div className="flex gap-1">
        {weeks.map((week, weekIndex) => (
          <div key={weekIndex} className="flex flex-col gap-1">
            {week.map((day, dayIndex) => (
              <div
                key={`${weekIndex}-${dayIndex}`}
                className={`w-3 h-3 rounded-sm ${getContributionColor(day.count)}`}
                title={`${day.count} contributions on ${day.date}`}
              />
            ))}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-2 mt-4 text-sm text-gray-600">
        <span>Less</span>
        <div className="flex gap-1">
          <div className="w-3 h-3 rounded-sm bg-gray-100" />
          <div className="w-3 h-3 rounded-sm bg-green-100" />
          <div className="w-3 h-3 rounded-sm bg-green-300" />
          <div className="w-3 h-3 rounded-sm bg-green-500" />
          <div className="w-3 h-3 rounded-sm bg-green-700" />
        </div>
        <span>More</span>
      </div>
    </div>
  );
};

export default ContributionHeatmap;