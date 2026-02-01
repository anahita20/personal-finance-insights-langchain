import React, { useState } from 'react';

const RecentTransactions = ({ transactions }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div style={{ marginTop: '32px' }}>
      <div 
        style={{ 
          background: '#fff',
          border: '1px solid #f0f0f0',
          borderRadius: '24px',
          padding: '24px'
        }}
      >
        <div 
          onClick={() => setIsOpen(!isOpen)} 
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between', 
            cursor: 'pointer',
            marginBottom: isOpen ? '16px' : '0'
          }}
        >
          <h3 style={{ margin: 0 }}>Recent Transactions</h3>
          <span style={{ fontSize: '12px', color: '#666' }}>{isOpen ? 'Hide' : 'Show'}</span>
        </div>
        
        {isOpen && (
          <div className="overflow-hidden">
            <table style={{ width: '100%', fontSize: '14px' }}>
              <thead>
                <tr style={{ background: '#f9fafb', textAlign: 'left' }}>
                  <th style={{ padding: '12px 16px', fontWeight: '600', color: '#666' }}>Date</th>
                  <th style={{ padding: '12px 16px', fontWeight: '600', color: '#666' }}>Description</th>
                  <th style={{ padding: '12px 16px', fontWeight: '600', color: '#666' }}>Category</th>
                  <th style={{ padding: '12px 16px', fontWeight: '600', color: '#666', textAlign: 'right' }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {transactions.slice(0, 5).map((t, i) => (
                  <tr key={i} style={{ borderTop: '1px solid #eee' }}>
                    <td style={{ padding: '12px 16px' }}>{t.Date || t.date}</td>
                    <td style={{ padding: '12px 16px' }}>{t.Description || t.description}</td>
                    <td style={{ padding: '12px 16px' }}><span style={{ background: '#f3f4f6', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' }}>{t.Category || t.category}</span></td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', fontWeight: '500' }}>${parseFloat(t.Amount || t.amount).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default RecentTransactions;