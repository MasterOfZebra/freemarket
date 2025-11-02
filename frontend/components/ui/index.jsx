import React from 'react';

// Card Component
/**
 * @typedef {Object} CardProps
 * @property {string} [className]
 * @property {React.ReactNode} children
 */

export const Card = ({ className = '', children }) => {
  return (
    <div className={`bg-white rounded-lg shadow ${className}`}>
      {children}
    </div>
  );
};

// Button Component
/**
 * @typedef {Object} ButtonProps
 * @property {React.ReactNode} children
 * @property {function(): void} [onClick]
 * @property {'primary'|'secondary'|'danger'} [variant]
 * @property {'sm'|'md'|'lg'} [size]
 * @property {boolean} [loading]
 * @property {string} [className]
 * @property {'button'|'submit'|'reset'} [type]
 */

export const Button = ({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  loading = false,
  className = '',
  type = 'button',
}) => {
  const baseClasses = 'px-4 py-2 rounded font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed';

  const variantClasses = {
    primary: 'bg-blue-500 text-white hover:bg-blue-600',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
    danger: 'bg-red-500 text-white hover:bg-red-600',
  };

  const sizeClasses = {
    sm: 'px-2 py-1 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={loading}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {loading ? 'Загрузка...' : children}
    </button>
  );
};

// Input Component
/**
 * @typedef {Object} InputProps
 * @property {string} [label]
 * @property {string} [placeholder]
 * @property {string} value
 * @property {function(string): void} onChange
 * @property {string} [type]
 * @property {number} [minLength]
 * @property {number} [maxLength]
 * @property {number} [min]
 * @property {number} [max]
 * @property {string} [className]
 */

export const Input = ({
  label,
  placeholder,
  value,
  onChange,
  type = 'text',
  minLength,
  maxLength,
  min,
  max,
  className = '',
}) => {
  return (
    <div className="flex flex-col">
      {label && <label className="mb-1 text-sm font-medium text-gray-700">{label}</label>}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        minLength={minLength}
        maxLength={maxLength}
        min={min}
        max={max}
        className={`px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
      />
    </div>
  );
};

// Select Component
/**
 * @typedef {Object} SelectOption
 * @property {string} value
 * @property {string} label
 */

/**
 * @typedef {Object} SelectProps
 * @property {string} [label]
 * @property {string} value
 * @property {function(string): void} onChange
 * @property {SelectOption[]} options
 * @property {string} [className]
 */

export const Select = ({
  label,
  value,
  onChange,
  options,
  className = '',
}) => {
  return (
    <div className="flex flex-col">
      {label && <label className="mb-1 text-sm font-medium text-gray-700">{label}</label>}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${className}`}
      >
        <option value="">Выберите...</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
};

// Textarea Component
/**
 * @typedef {Object} TextareaProps
 * @property {string} [label]
 * @property {string} [placeholder]
 * @property {string} value
 * @property {function(string): void} onChange
 * @property {number} [maxLength]
 * @property {number} [rows]
 * @property {string} [className]
 */

export const Textarea = ({
  label,
  placeholder,
  value,
  onChange,
  maxLength,
  rows = 3,
  className = '',
}) => {
  return (
    <div className="flex flex-col">
      {label && <label className="mb-1 text-sm font-medium text-gray-700">{label}</label>}
      <textarea
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        maxLength={maxLength}
        rows={rows}
        className={`px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none ${className}`}
      />
    </div>
  );
};

// Alert Component
/**
 * @typedef {Object} AlertProps
 * @property {'error'|'warning'|'info'|'success'} [type]
 * @property {React.ReactNode} children
 * @property {string} [className]
 */

export const Alert = ({
  type = 'info',
  children,
  className = '',
}) => {
  const typeClasses = {
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-green-50 border-green-200 text-green-800',
  };

  return (
    <div className={`p-4 border rounded-md ${typeClasses[type]} ${className}`}>
      {children}
    </div>
  );
};

