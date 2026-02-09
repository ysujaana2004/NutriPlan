import { useState } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from 'recharts';

const PIE_DATA = [
  { name: 'Breakfast', value: 28, color: '#4CAF50' },
  { name: 'Lunch', value: 35, color: '#81C784' },
  { name: 'Dinner', value: 37, color: '#A3E4A6' },
];

const BAR_DATA = [
  { week: 'Feb 3', spent: 72, budget: 100 },
  { week: 'Feb 10', spent: 45, budget: 100 },
  { week: 'Feb 17', spent: 88, budget: 100 },
];

const LINE_DATA = [
  { day: 'Mon', score: 85 },
  { day: 'Tue', score: 88 },
  { day: 'Wed', score: 82 },
  { day: 'Thu', score: 90 },
  { day: 'Fri', score: 87 },
  { day: 'Sat', score: 91 },
  { day: 'Sun', score: 89 },
];

export function Analytics() {
  const [range, setRange] = useState<'week' | 'month'>('week');
  const saved = 15; // mock

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <div className="flex rounded-lg border border-gray-200 bg-white p-0.5">
          <button
            onClick={() => setRange('week')}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${
              range === 'week' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Week
          </button>
          <button
            onClick={() => setRange('month')}
            className={`rounded-md px-3 py-1.5 text-sm font-medium ${
              range === 'month' ? 'bg-primary text-white' : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Month
          </button>
        </div>
      </div>

      <div className="mb-6 rounded-xl border border-green-200 bg-green-50 p-4">
        <p className="text-sm font-medium text-green-800">
          You saved <span className="font-bold">${saved}</span> this {range} compared to average!
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <h3 className="mb-4 font-semibold text-gray-900">Calorie distribution per meal type</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={PIE_DATA}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  {PIE_DATA.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <h3 className="mb-4 font-semibold text-gray-900">Weekly spend vs budget</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={BAR_DATA}>
                <XAxis dataKey="week" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="spent" fill="#4CAF50" name="Spent" radius={[4, 4, 0, 0]} />
                <Bar dataKey="budget" fill="#E0E0E0" name="Budget" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-xl border border-gray-200 bg-white p-4">
        <h3 className="mb-4 font-semibold text-gray-900">Nutrition score over time</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={LINE_DATA}>
              <XAxis dataKey="day" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="score" stroke="#4CAF50" strokeWidth={2} name="Score" dot />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
