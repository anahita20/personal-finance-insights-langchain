import React, { useState } from "react";

const TabsContext = React.createContext(null);

export function Tabs({ defaultValue, className, children, onValueChange, ...props }) {
  const [activeTab, setActiveTab] = useState(defaultValue);

  const handleTabChange = (value) => {
    setActiveTab(value);
    if (onValueChange) {
      onValueChange(value);
    }
  };

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab: handleTabChange }}>
      <div className={className} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
}

export function TabsList({ className, children, ...props }) {
  return (
    <div className={`inline-flex items-center justify-center gap-2 ${className || ""}`} {...props}>
      {children}
    </div>
  );
}

export function TabsTrigger({ value, className, children, ...props }) {
  const { activeTab, setActiveTab } = React.useContext(TabsContext);
  const isActive = activeTab === value;
  
  return (
    <button
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border ${isActive ? "bg-[#0052ff] text-white border-[#0052ff] shadow-sm" : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:text-gray-900"} ${className || ""}`}
      onClick={() => setActiveTab(value)}
      {...props}
    >
      {children}
    </button>
  );
}