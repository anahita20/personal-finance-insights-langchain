import React, { useEffect, useState } from 'react';
import { Card } from "./card";
import { Tabs, TabsList, TabsTrigger } from "./tabs";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, CartesianGrid } from 'recharts';
import "../styles/Styles.css"

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const ExpensesSummary = () => {
  const [data, setData] = useState({ by_category: [], by_day: [], top_descriptions: [] });
  const [period, setPeriod] = useState('month');
  const [insights, setInsights] = useState({ by_category: null, by_day: null, top_descriptions: null });
  const [loadingInsights, setLoadingInsights] = useState({ by_category: false, by_day: false, top_descriptions: false });

  useEffect(() => {
    setInsights({ by_category: null, by_day: null, top_descriptions: null });
    fetch(`http://localhost:8080/api/analytics/expense-summary?period=${period}`)
      .then(res => res.json())
      .then(response => {
        // Handle new response structure
        let categoryData = response.by_category || [];
        
        if (categoryData.length > 5) {
            const top5 = categoryData.slice(0, 5);
            const othersValue = categoryData.slice(5).reduce((sum, item) => sum + item.value, 0);
            categoryData = [...top5, { category: 'others', value: othersValue }];
        }

        setData({
            by_category: categoryData,
            by_day: response.by_day || [],
            top_descriptions: response.top_descriptions || []
        });

        if (response.insight_inputs) {
          Object.entries(response.insight_inputs).forEach(([key, input]) => {
            setLoadingInsights(prev => ({ ...prev, [key]: true }));
            fetch('http://localhost:8080/api/insights', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(input)
            })
            .then(res => res.json())
            .then(data => setInsights(prev => ({ ...prev, [key]: data.insight })))
            .catch(err => console.error(`Failed to fetch insight for ${key}:`, err))
            .finally(() => setLoadingInsights(prev => ({ ...prev, [key]: false })));
          });
        }
      })
      .catch(err => console.error("Failed to fetch expense summary:", err));
  }, [period]);

  const renderInsight = (key) => (
    <div className="mt-3 min-h-[20px]">
      {loadingInsights[key] && <div className="text-xs text-gray-500 italic">Generating insight...</div>}
      {!loadingInsights[key] && insights[key] && (
        <div className="text-xs text-gray-700 bg-slate-50 p-2 rounded border border-slate-100">
           <span className="text-xl">💡</span> {insights[key]}
        </div>
      )}
    </div>
  );

  return (
    <Card className="p-6 flex flex-col">
      <div className="flex items-center gap-4 mb-6">
        <h3 className="text-lg font-semibold expense-analysis-title">Expense Analysis</h3>
        <Tabs defaultValue="month" onValueChange={setPeriod}>
          <TabsList>
            <TabsTrigger value="week">Week</TabsTrigger>
            <TabsTrigger value="month">Month</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
      
      <div className="grid grid-cols-3 gap-5">
        {/* Column 1: By Category */}
        <div className="flex flex-col">
            <h4 className="text-sm font-medium text-gray-500 mb-4 text-center">By Category</h4>
            <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                    <Pie
                    data={data.by_category}
                    cx="50%"
                    cy="50%"
                    innerRadius={0}
                    outerRadius={80}
                    dataKey="value"
                    nameKey="category"
                    label={(entry) => entry.category}
                    >
                    {data.by_category.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                    </Pie>
                    <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                </PieChart>
                </ResponsiveContainer>
            </div>
            {renderInsight('by_category')}
        </div>

        {/* Column 2: Top Descriptions */}
        <div className="flex flex-col">
            <h4 className="text-sm font-medium text-gray-500 mb-4 text-center">Top Expenses</h4>
            <div className="h-[250px] overflow-auto">
                {data.top_descriptions.map((item, i) => (
                    <div key={i} className="top-expense-item flex justify-between items-center border border-gray-100 rounded-lg bg-gray-50">
                        <div className="flex items-center gap-2 overflow-hidden">
                            
                            <span className="text-sm font-medium truncate" title={item.description}>{item.description}</span>
                        </div>
                        <span className="text-sm font-bold whitespace-nowrap">${item.total.toFixed(2)}</span>
                    </div>
                ))}
                {data.top_descriptions.length === 0 && <div className="text-center text-gray-400 text-sm mt-10">No data</div>}
            </div>
            {renderInsight('top_descriptions')}
        </div>

        {/* Column 3: By Day */}
        <div className="flex flex-col border-l border-gray-200 pl-6">
            <h4 className="text-sm font-medium text-gray-500 mb-4 text-center">When You Spend the Most</h4>
            <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.by_day}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="day" tick={{fontSize: 12}} interval={0} />
                        <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                        <Bar dataKey="value" fill="#8884d8" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
            {renderInsight('by_day')}
        </div>
      </div>
    </Card>
  );
};

export default ExpensesSummary;