import React, { useState, useEffect } from 'react';
import { Card } from "./card";
import { Button } from "./button";

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const limit = 20;

  useEffect(() => {
    setLoading(true);
    fetch(`http://localhost:8080/api/transactions?page=${page}&limit=${limit}`)
      .then(res => res.json())
      .then(data => {
        setTransactions(data.data || []);
        setTotalPages(Math.ceil((data.total || 0) / limit));
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch transactions:", err);
        setLoading(false);
      });
  }, [page]);

  return (
    <div style={{ marginTop: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0 }}>All Transactions</h3>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Button 
            variant="outline" 
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1 || loading}
          >
            Previous
          </Button>
          <span style={{ fontSize: '14px', color: '#666' }}>
            Page {page} of {totalPages || 1}
          </span>
          <Button 
            variant="outline" 
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages || loading}
          >
            Next
          </Button>
        </div>
      </div>
      <Card className="overflow-hidden">
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ background: '#f9fafb', textAlign: 'left' }}>
              <th style={{ padding: '12px 16px', fontWeight: '600', color: '#666' }}>Date</th>
              <th style={{ padding: '12px 16px', fontWeight: '600', color: '#666' }}>Description</th>
              <th style={{ padding: '12px 16px', fontWeight: '600', color: '#666' }}>Category</th>
              <th style={{ padding: '12px 16px', fontWeight: '600', color: '#666', textAlign: 'right' }}>Amount</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((t, i) => (
              <tr key={i} style={{ borderTop: '1px solid #eee' }}>
                <td style={{ padding: '12px 16px' }}>{t.Date || t.date}</td>
                <td style={{ padding: '12px 16px' }}>{t.Description || t.description}</td>
                <td style={{ padding: '12px 16px' }}><span style={{ background: '#f3f4f6', padding: '2px 8px', borderRadius: '4px', fontSize: '12px' }}>{t.Category || t.category}</span></td>
                <td style={{ padding: '12px 16px', textAlign: 'right', fontWeight: '500' }}>${parseFloat(t.Amount || t.amount).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
};

export default Transactions;