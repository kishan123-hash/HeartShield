import React from 'react';
import { AlertTriangle, PhoneCall } from 'lucide-react';

export default function EmergencyBanner({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="bg-red-50 border-l-4 border-red-600 p-4 rounded-xl shadow-md my-4 animate-pulse">
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="w-6 h-6 text-red-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-bold text-red-900 tracking-tight">CRITICAL EMERGENCY DETECTED</h4>
            <div className="text-xs text-red-800 mt-1 leading-relaxed whitespace-pre-line">
              {message}
            </div>
            <div className="mt-3 flex items-center space-x-3">
              <a
                href="tel:112"
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-lg shadow-xs"
              >
                <PhoneCall className="w-3.5 h-3.5" />
                <span>Call Emergency (112 / 911)</span>
              </a>
            </div>
          </div>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-red-400 hover:text-red-600 text-sm font-bold ml-4"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}
