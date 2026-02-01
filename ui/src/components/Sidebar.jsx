import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Sidebar = () => {
  const location = useLocation();
  const navItems = [
    { label: 'Dashboard', path: '/' },
    { label: 'Chat', path: '/chat' },
    { label: 'Goals', path: '/budgeting' },
    { label: 'Transactions', path: '/transactions' },
    
  ];
  const toolItems = ['Tax Reserve', 'Invoices'];

  return (
    <aside style={{ width: '260px', borderRight: '1px solid #eee', padding: '24px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ fontWeight: 'bold', color: '#0052ff', fontSize: '28px', marginBottom: '40px' }}>FinAI</div>
      
      <nav style={{ flex: 1 }}>
        {navItems.map(item => {
          const isActive = location.pathname === item.path;
          return (
            <Link key={item.label} to={item.path} style={{ textDecoration: 'none' }}>
              <div style={{ padding: '12px 16px', borderRadius: '8px', cursor: 'pointer', marginBottom: '8px', color: isActive ? '#0052ff' : '#666', background: isActive ? '#f0f4ff' : 'transparent' }}>
                {item.label}
              </div>
            </Link>
          );
        })}
        
      </nav>
      
      </aside>
  );
};

export default Sidebar;
