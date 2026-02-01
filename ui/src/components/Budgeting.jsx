import React, { useState, useEffect } from 'react';
import { Card } from "./card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import GoalForecastChart from '/Users/anahitadinesh/Desktop/panw/eduQuery/ui/src/components/GoalForecastChart.jsx';

export function Progress({ value, className, indicatorColor, ...props }) {
  return (
    <div className={`relative h-4 w-full overflow-hidden rounded-full bg-secondary ${className || ""}`} {...props}>
      <div
        className="h-full w-full flex-1 bg-primary transition-all"
        style={{ transform: `translateX(-${100 - (value || 0)}%)`, backgroundColor: indicatorColor }}
      />
    </div>
  );
}

const getLast12Months = () => {
  const months = [];
  const date = new Date();
  for (let i = 0; i < 12; i++) {
    const d = new Date(date.getFullYear(), date.getMonth() - i, 1);
    const value = d.toISOString().slice(0, 7); // YYYY-MM
    const label = d.toLocaleString('default', { month: 'long', year: 'numeric' });
    months.push({ value, label });
  }
  return months;
};

const Budgeting = () => {
  const [budgets, setBudgets] = useState([]);
  const [months] = useState(getLast12Months());
  const [selectedMonth, setSelectedMonth] = useState(months[0].value);

  useEffect(() => {
    fetch(`http://localhost:8080/api/budgets?month=${selectedMonth}`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setBudgets(data);
      })
      .catch(err => console.error("Failed to fetch budgets:", err));
  }, [selectedMonth]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const percentage = data.limit > 0 ? (data.spent / data.limit) * 100 : 0;
      
      return (
        
        <div className="bg-white p-3 border border-gray-200 rounded shadow-sm">
          <p className="font-bold mb-2">{label}</p>
          <div className="text-sm text-blue-600">Spent: ${data.spent.toLocaleString()}</div>
          <div className="text-sm text-gray-500">Limit: ${data.limit.toLocaleString()}</div>
          <div className={`text-sm font-bold mt-1 ${data.spent > data.limit ? 'text-red-500' : 'text-green-500'}`}>
            {percentage.toFixed(0)}% Used
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="mt-8 px-4">
      <div style={{ display: 'grid', gap: '24px', marginBottom: '32px', marginTop: '32px'  }}>
        <GoalForecastChart />
      </div>
      <div className="flex justify-between items-center mb-6 border border-gray-300"
      style={{padding:'5px'}}>
        <h3 className="text-xl font-bold text-slate-800" style={{padding:'10px'}}>Monthly Budgets Overview</h3>
        <select
          
          value={selectedMonth}
          onChange={(e) => setSelectedMonth(e.target.value)}
          className="rounded-md p-2 text-sm bg-white"
        >
          {months.map((m) => (
            <option key={m.value} value={m.value}>{m.label}</option>
          ))}
        </select>
      
      </div>
      {/* Visualization: Bar Chart comparing Spent vs Limit */}
      <Card className="p-6 mb-8">
        <div className="h-[400px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={budgets}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="category" />
            <YAxis />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'transparent' }} />
            <Legend />
            <Bar dataKey="spent" name="Spent" fill="9246d1" radius={[4, 4, 0, 0]}>
              {budgets.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.spent > entry.limit ? '#ef4444' : '#9246d1'} />
              ))}
            </Bar>
            <Bar dataKey="limit" name="Limit" fill="#4c99ff" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        </div>
      </Card>
      

      {/* Detailed Cards */}
      {/* <BudgetDashboard budgets={budgets} />                */}
      
    </div> 
  );
};

export default Budgeting;