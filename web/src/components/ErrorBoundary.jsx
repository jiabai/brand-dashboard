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

import { Alert, AlertDescription, AlertTitle } from './ui/alert.jsx';
import { Button } from './ui/button.jsx';
import { cn } from '@/lib/cn';

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
        <div className="flex min-h-80 items-center justify-center p-6">
          <Alert variant="destructive" className="w-[456px] h-[388px]">
            <AlertTitle>出错了</AlertTitle>
            <AlertDescription className="flex flex-col gap-3">
              <span>组件渲染时遇到了问题。</span>
              <Button className="w-fit" variant="outline" onClick={this.handleReset}>
                重试
              </Button>
              {isDevelopment ? (
                <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-md bg-muted p-3 text-xs text-foreground">
                  {this.state.error ? String(this.state.error) : null}
                  {this.state.errorInfo?.componentStack
                    ? `\n\n${this.state.errorInfo.componentStack}`
                    : null}
                </pre>
              ) : null}
            </AlertDescription>
          </Alert>
        </div>
      );
    }

    return <div className={cn(this.props.className)}>{this.props.children}</div>;
  }
}

export default ErrorBoundary;
