// src/components/ui/card.jsx
import React from "react";

export function Card({ children, className = "" }) {
  return (
    <div className={`rounded-xl border p-4 bg-white shadow-sm ${className}`}>
      {children}
    </div>
  );
}
