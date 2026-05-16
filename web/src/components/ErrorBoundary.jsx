/**
 * Error Boundary Component
 * Catches and handles errors in child components with graceful fallback UI
 *
 * @component
 * @example
 * return (
 *   <ErrorBoundary>
 *     <YourComponent />
 *   </ErrorBoundary>
 * );
 */

import React, { useCallback } from 'react';
import { Button, Result, Typography } from 'antd';

const isDevelopment = import.meta.env.DEV;

/**
 * ErrorBoundary component that catches JavaScript errors in child components
 * and displays a fallback UI instead of crashing the entire app
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components to wrap
 * @param {React.ReactNode} props.fallback - Custom fallback UI (optional)
 * @param {Function} props.onError - Error callback function (optional)
 * @returns {JSX.Element} Error boundary wrapper
 */
const ErrorBoundary = ({ children, fallback, onError, className }) => {
  /**
   * Catch errors thrown in child components
   */
  const handleError = useCallback((error, errorInfo) => {
    console.error('Error caught by boundary:', error, errorInfo);

    // Call custom error handler if provided
    if (typeof onError === 'function') {
      onError(error, errorInfo);
    }
  }, [onError]);

  // For a complete error boundary implementation, we need to use the class component
  // This functional component provides a wrapper for consistency
  return (
    <ErrorBoundaryClass
      onError={handleError}
      fallback={fallback}
      className={className}
    >
      {children}
    </ErrorBoundaryClass>
  );
};

/**
 * Class-based Error Boundary implementation
 * This provides the actual error catching functionality
 */
class ErrorBoundaryClass extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error and call error handler
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    this.setState({
      error,
      errorInfo
    });

    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  /**
   * Reset error state
   */
  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI if provided
      if (this.props.fallback) {
        return typeof this.props.fallback === 'function'
          ? this.props.fallback(this.state.error, this.state.errorInfo, this.handleReset)
          : this.props.fallback;
      }

      // Default error fallback UI
      return (
        <Result
          status="error"
          title="出错了"
          subTitle="组件渲染时遇到了问题"
          extra={
            <Button type="primary" onClick={this.handleReset}>
              重试
            </Button>
          }
        >
          {isDevelopment ? (
            <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
              {this.state.error ? String(this.state.error) : null}
              {this.state.errorInfo?.componentStack
                ? `\n\n${this.state.errorInfo.componentStack}`
                : null}
            </Typography.Paragraph>
          ) : null}
        </Result>
      );
    }

    return <div className={this.props.className}>{this.props.children}</div>;
  }
}

export default ErrorBoundary;
