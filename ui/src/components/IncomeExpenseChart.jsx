import React, { useEffect, useState } from 'react';
import { Card } from "./card";
import { Tabs, TabsList, TabsTrigger } from "./tabs";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const IncomeExpenseChart = () => {
  const [data, setData] = useState([]);
  const [period, setPeriod] = useState('month');
  const [insight, setInsight] = useState(null);
  const [loadingInsight, setLoadingInsight] = useState(false);

  useEffect(() => {
    setInsight(null);
    fetch(`http://localhost:8080/api/analytics/income-vs-expenses?period=${period}`)
      .then(res => res.json())
      .then(response => {
        const rawData = response.data || [];
        // Format period for display
        const formattedData = rawData.map((item) => {
          // item.date is "YYYY-MM-DD"
          const dateObj = new Date(item.date);
          const name = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          return {
            ...item,
            name: name,
            // Split data into history and forecast series
            incomeHistory: !item.isForecast ? item.income : null,
            expenseHistory: !item.isForecast ? item.expense : null,
            incomeForecast: item.isForecast ? item.income : null,
            expenseForecast: item.isForecast ? item.expense : null,
          };
        });

        // Bridge the gap: Ensure the last history point connects to the first forecast point
        for (let i = 0; i < formattedData.length - 1; i++) {
          if (!formattedData[i].isForecast && formattedData[i + 1].isForecast) {
            // Assign the current history values to the forecast keys for this point
            // so the dashed line starts exactly where the solid line ends.
            formattedData[i].incomeForecast = formattedData[i].income;
            formattedData[i].expenseForecast = formattedData[i].expense;
          }
        }

        setData(formattedData);

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
      .catch(err => console.error("Failed to fetch chart data:", err));
  }, [period]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-sm text-sm">
          <p className="font-bold mb-2">{label} {d.isForecast ? <span className="text-blue-600 text-xs ml-1">(Forecast)</span> : ''}</p>
          <div className="text-emerald-600">Income: ${d.income?.toFixed(2)}</div>
          <div className="text-red-500">Expense: ${d.expense?.toFixed(2)}</div>
          {d.anomaly?.income && <div className="text-emerald-600 font-bold text-xs mt-1">⚠️ Income Anomaly</div>}
          {d.anomaly?.expense && <div className="text-red-500 font-bold text-xs mt-1">⚠️ Expense Anomaly</div>}
        </div>
      );
    }
    return null;
  };

  const CustomDot = (props) => {
    const { cx, cy, payload, dataKey } = props;
    const isIncome = dataKey.includes('income');
    const isExpense = dataKey.includes('expense');

    // Check if this specific metric has an anomaly
    const hasAnomaly = payload.anomaly && (
      (isIncome && payload.anomaly.income) ||
      (isExpense && payload.anomaly.expense)
    );

    if (hasAnomaly) {
      const color = isIncome ? "#2ecc71" : "#ef4444";
      return (
        <g>
          <circle cx={cx} cy={cy} r={10} fill={color} fillOpacity={0.3} />
          <circle cx={cx} cy={cy} r={6} fill={color} stroke="white" strokeWidth={2} />
        </g>
      );
    }
    return null;
  };

  return (
    <Card className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Income vs Expenses ({period === 'month' ? 'Last 30 Days' : 'Last 7 Days'})</h3>
        <Tabs defaultValue="month" onValueChange={setPeriod}>
          <TabsList>
            <TabsTrigger value="week">Week</TabsTrigger>
            <TabsTrigger value="month">Month</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{
              top: 20,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" minTickGap={30} />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Legend />

            <Line type="monotone" dataKey="incomeHistory" name="Income" stroke="#2ecc71" strokeWidth={2} dot={<CustomDot />} />
            <Line type="monotone" dataKey="incomeForecast" name="Income (Forecast)" stroke="#2ecc71" strokeWidth={2} strokeDasharray="5 5" dot={false} />

            <Line type="monotone" dataKey="expenseHistory" name="Expense" stroke="#ef4444" strokeWidth={2} dot={<CustomDot />} />
            <Line type="monotone" dataKey="expenseForecast" name="Expense (Forecast)" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4">
        {loadingInsight && <div className="text-sm text-gray-500 italic">Generating insights...</div>}
        {!loadingInsight && insight && (
          <div className="text-sm text-gray-700 bg-slate-50 p-3 rounded border border-slate-100">
            <span className="text-xl">💡</span> {insight}
          </div>
        )}
      </div>
    </Card>
  );
};

export default IncomeExpenseChart;