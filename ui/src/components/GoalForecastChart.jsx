import React, { useState, useEffect } from 'react';
import { Card } from "/Users/anahitadinesh/Desktop/panw/eduQuery/ui/src/Components/card.jsx";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const GoalForecastChart = () => {
  const [goals, setGoals] = useState([]);
  const [selectedGoalId, setSelectedGoalId] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [insight, setInsight] = useState(null);
  const [loadingInsight, setLoadingInsight] = useState(false);

  // Fetch list of goals
  useEffect(() => {
    fetch('http://localhost:8080/api/goals')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setGoals(data);
          setSelectedGoalId(data[0].id);
        }
      })
      .catch(err => console.error("Failed to fetch goals:", err));
  }, []);

  // Fetch forecast data when goal changes
  useEffect(() => {
    if (!selectedGoalId) return;

    setInsight(null);
    
    fetch(`http://localhost:8080/api/analytics/goal-forecast?goal_id=${selectedGoalId}`)
      .then(res => res.json())
      .then(response => {
        setChartData(response.data || []);
        
        if (response.insight_input) {
          setLoadingInsight(true);
          fetch('http://localhost:8080/api/insights', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(response.insight_input)
          })
          .then(res => res.json())
          .then(data => setInsight(data.insight))
          .catch(err => console.error("Failed to fetch insight:", err))
          .finally(() => setLoadingInsight(false));
        }
      })
      .catch(err => console.error("Failed to fetch forecast:", err));
  }, [selectedGoalId]);

  return (
    <Card className="p-6">
      <div className="flex justify-between items-center mb-6" style={{padding:'5px'}}>
        <h3 className="text-lg font-semibold" style={{padding: '10px'}}>Goal Forecasting</h3>
        <select 
          className="border border-gray-300 rounded-md p-2 text-sm bg-white min-w-[150px]"
          value={selectedGoalId || ''}
          
          onChange={(e) => setSelectedGoalId(e.target.value)}
        >
          {goals.map(g => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>
      </div>

      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
            <Legend />
            
            {/* Actual Progress */}
            <Line type="monotone" dataKey="actual" name="Actual Progress" stroke="#2ecc71" strokeWidth={3} dot={{ r: 4 }} />
            
            {/* Forecasted Path */}
            <Line type="monotone" dataKey="forecast" name="Forecasted Path" stroke="#3b82f6" strokeWidth={2} strokeDasharray="5 5" dot={false} />
            
            {/* Ideal Path */}
            <Line type="monotone" dataKey="ideal" name="Ideal Path" stroke="#9ca3af" strokeWidth={2} strokeDasharray="3 3" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4">
        {loadingInsight && <div className="text-sm text-gray-500 italic">Generating forecast insight...</div>}
        {!loadingInsight && insight && (
          <div className="mt-2 text-sm text-gray-700 bg-slate-50 p-3 rounded border border-slate-100">
            <span className="text-xl">💡</span> {insight}
          </div>
        )}
      </div>
    </Card>
  );
};

export default GoalForecastChart;