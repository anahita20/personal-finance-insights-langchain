import React from 'react';

const StatCard = ({ title, value, tag, tagColor, trend, trendDirection }) => {
  // trendDirection: 'up' | 'down'
  // For assets (Checking): Up is Green, Down is Red
  // For liabilities (Cards): Up is Red, Down is Green
  
  const isPositive = trendDirection === 'up';
  const arrowColor = isPositive ? '#2ecc71' : '#ef4444'; // Green : Red
  const arrow = isPositive ? '↑' : '↓';

  return (
  <div style={{ background: '#fff', padding: '24px', borderRadius: '20px', border: '1px solid #f0f0f0', flex: 1 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
      <div style={{ width: '40px', height: '40px', background: '#f9f9f9', borderRadius: '8px' }}></div>
      <span style={{ color: tagColor, fontSize: '12px', fontWeight: 'bold' }}>{tag}</span>
    </div>
    <div style={{ color: '#888', fontSize: '12px', textTransform: 'uppercase' }}>{title}</div>
    <div style={{ fontSize: '22px', fontWeight: 'bold', marginTop: '4px' }}>{value}</div>
    {trend && (
      <div style={{ display: 'flex', alignItems: 'center', marginTop: '8px', fontSize: '12px' }}>
        <span style={{ color: arrowColor, fontWeight: 'bold', marginRight: '4px' }}>{arrow} {trend}</span>
        <span style={{ color: '#888' }}>since last month</span>
      </div>
    )}
  </div>
);
};

export default StatCard;