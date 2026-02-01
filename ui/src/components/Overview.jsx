import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import StatCard from './StatCard';
import RecentTransactions from './RecentTransactions';
import IncomeExpenseChart from './IncomeExpenseChart';
import ExpensesSummary from './ExpensesSummary';
import GoalForecastChart from '/Users/anahitadinesh/Desktop/panw/eduQuery/ui/src/components/GoalForecastChart.jsx';

const Overview = () => {
  const { transactions } = useOutletContext();
  const [accounts, setAccounts] = useState([]);

  useEffect(() => {
    fetch('http://localhost:8080/api/accounts')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setAccounts(data);
        }
      })
      .catch(err => console.error("Failed to fetch accounts:", err));
  }, []);

  const getAccountData = (name) => {
    const account = accounts.find(a => a.name === name);
    if (!account) return { value: '...', trend: null, trendDirection: null };
    
    const balance = account.type === 'credit' ? Math.abs(account.balance) : account.balance;
    const value = `$${balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    
    
    const trendVal = account.trend || 0;
    const absTrend = Math.abs(trendVal).toFixed(1) + '%';
    
    let trendDirection = 'up'; // Default arrow direction
    let colorLogic = 'good'; // 'good' = green, 'bad' = red
    
    if (account.type === 'depository') {
        // Asset: Increase is Good (Green Up), Decrease is Bad (Red Down)
        if (trendVal >= 0) { trendDirection = 'up'; colorLogic = 'good'; }
        else { trendDirection = 'down'; colorLogic = 'bad'; }
    } else {
        // Liability: Increase is Bad (Red Up), Decrease is Good (Green Down)
        if (trendVal >= 0) { trendDirection = 'up'; colorLogic = 'bad'; }
        else { trendDirection = 'down'; colorLogic = 'good'; }
    }
    
    
    return { value, trend: absTrend, trendDirection, colorLogic };
  };
  
  const checking = getAccountData('checking');
  const platinum = getAccountData('platinumcard');
  const silver = getAccountData('silvercard');

  return (
    <>
      {/* AI Coach Banner 
      <div style={{ border: '2px solid #0052ff', borderRadius: '24px', padding: '32px', marginBottom: '32px', display: 'flex', alignItems: 'center', gap: '24px', position: 'relative', overflow: 'hidden' }}>
        <div style={{ background: '#0052ff', width: '60px', height: '60px', borderRadius: '12px' }}></div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <strong style={{ fontSize: '18px' }}>AI Coach Recommendation</strong>
            <span style={{ background: '#dbeafe', color: '#0052ff', fontSize: '10px', padding: '2px 8px', borderRadius: '4px' }}>PRIORITY</span>
          </div>
          <p style={{ color: '#444', fontStyle: 'italic', marginTop: '8px' }}>
            "You've spent 22% more on food delivery this month... reducing this could help you reach your 'Bali Trip' goal 2 weeks earlier."
          </p>
        </div>
        <button style={{ background: '#0052ff', color: '#fff', border: 'none', padding: '12px 24px', borderRadius: '12px', fontWeight: 'bold', cursor: 'pointer' }}>
          Opt-in Challenge
        </button>
      </div>
      */}

      {/* Stats Grid */}
      <div style={{ display: 'flex', gap: '24px', marginBottom: '32px' }}>
        <StatCard 
            title="Checking Account" 
            value={checking.value} 
            tag="Asset" 
            tagColor="#2ecc71" 
            trend={checking.trend}
            trendDirection={checking.colorLogic === 'good' ? 'up' : 'down'} 
        />
        <StatCard 
            title="Platinum Card" 
            value={platinum.value} 
            tag="Credit" 
            tagColor="#888" 
            trend={platinum.trend}
            trendDirection={platinum.colorLogic === 'good' ? 'up' : 'down'} 
        />
        <StatCard 
            title="Silver Card" 
            value={silver.value} 
            tag="Credit" 
            tagColor="#888" 
            trend={silver.trend}
            trendDirection={silver.colorLogic === 'good' ? 'up' : 'down'} 
        />
      </div>

      {/* Charts Section */}
      <div style={{ display: 'grid', gap: '24px', marginBottom: '32px' }}>
        <IncomeExpenseChart />
      </div>

      <div style={{ display: 'grid', gap: '24px', marginBottom: '32px' }}>
        <ExpensesSummary />
      </div>

      

      {/* Recent Transactions Section */}
      <RecentTransactions transactions={transactions} />
    </>
  );
};

export default Overview;