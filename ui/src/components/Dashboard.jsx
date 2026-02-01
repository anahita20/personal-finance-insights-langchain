import React, { useEffect, useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';

const Dashboard = () => {
  const [transactions, setTransactions] = useState([]);
  const [safeToSpend, setSafeToSpend] = useState(0);

  useEffect(() => {
    // Fetch only the top 5 transactions for the dashboard overview
    fetch('http://localhost:8080/api/transactions?limit=5')
      .then(res => res.json())
      .then(data => {
        console.log("Fetched transactions:", data);
        // Store all transactions
        if (Array.isArray(data)) setTransactions(data);
      })
      .catch(err => console.error("Failed to fetch transactions:", err));

    // Fetch budgets to calculate safe to spend
    fetch('http://localhost:8080/api/budgets')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          const totalLimit = data.reduce((acc, curr) => acc + curr.limit, 0);
          const totalSpent = data.reduce((acc, curr) => acc + curr.spent, 0);
          setSafeToSpend(totalLimit - totalSpent);
        }
      })
      .catch(err => console.error("Failed to fetch budgets:", err));
  }, []);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'Inter, sans-serif', color: '#1a1a1a' }}>
      <Sidebar />
      
      <main style={{ flex: 1, padding: '40px', background: '#fff' }}>
        {/* Header */}
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
          <div>
            <h1 style={{ margin: 0 }}>Hello, Alex 👋</h1>
          </div>
          <div style={{ background: '#f0f4ff', padding: '10px 20px', borderRadius: '30px', color: '#0052ff', fontWeight: 'bold' }}>
            Safe to spend: ${safeToSpend.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </header>

        <Outlet context={{ transactions }} />
      </main>
    </div>
  );
};

export default Dashboard;