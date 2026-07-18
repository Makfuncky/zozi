# Error Handling System

This document describes the comprehensive error handling system implemented in the ZOZI frontend application.

## Overview

The error handling system provides:
- Global error boundary for React component errors
- Automatic API error handling with toast notifications
- Custom hooks for consistent API interactions
- Global error handler for unhandled errors and promise rejections
- Error reporting and logging infrastructure

## Components

### 1. Enhanced Error Boundary (`ErrorBoundary.tsx`)

Catches React component errors and provides user-friendly error displays.

**Features:**
- Error ID generation for tracking
- Error reporting integration (ready for Sentry/LogRocket)
- Retry functionality
- Error details display in development
- Clipboard error reporting

**Usage:**
```tsx
<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>

<ErrorBoundary showReportButton onError={(error, info) => console.log(error)}>
  <YourComponent />
</ErrorBoundary>
```

### 2. API Error Handling (`api.ts`)

Enhanced API utilities with automatic error handling.

**Functions:**
- `handleApiError(error, context)` - Logs and processes API errors
- `getErrorMessage(data)` - Extracts user-friendly messages from API responses

### 3. Custom API Hooks (`useApi.ts`)

React hooks for consistent API interactions with automatic error handling.

**useApi Hook:**
```tsx
const { data, loading, error, execute } = useApi({
  showToastOnError: true,
  errorMessage: "Custom error message",
  successMessage: "Success!",
  onSuccess: (data) => console.log("Success", data),
  onError: (error) => console.log("Error", error)
});

// Usage
const result = await execute("/api/endpoint");
```

**useApiMutation Hook:**
```tsx
const { post, put, patch, delete: deleteMutation, loading, error } = useApiMutation({
  successMessage: "Saved successfully"
});

// Usage
await post("/api/items", { name: "New Item" });
await put("/api/items/1", { name: "Updated Item" });
await delete("/api/items/1");
```

### 4. Global Error Handler (`globalErrorHandler.ts`)

Handles unhandled errors and promise rejections application-wide.

**Features:**
- Automatic initialization on app start
- Unhandled promise rejection handling
- Uncaught error handling
- Manual error reporting

**Usage:**
```tsx
import { globalErrorHandler } from "@/lib/globalErrorHandler";

// Manual error reporting
globalErrorHandler.reportError(new Error("Something went wrong"), {
  userId: "123",
  action: "checkout"
});

// Issue reporting
globalErrorHandler.reportIssue("User encountered validation error", "warning", {
  field: "email",
  value: "invalid"
});
```

### 5. Toast Notifications (`toastStore.ts`)

Integrated toast system for user feedback.

**Usage:**
```tsx
import { useToastStore } from "@/lib/toastStore";

const { addToast } = useToastStore();
addToast("Operation successful", "success");
addToast("Something went wrong", "error");
addToast("Please check your input", "info");
```

## Migration Guide

### From Manual Error Handling

**Before:**
```tsx
const handleSubmit = async () => {
  try {
    const res = await apiFetch("/api/endpoint");
    if (!res.ok) {
      const error = await res.json();
      setError(getErrorMessage(error));
      addToast(getErrorMessage(error), "error");
      return;
    }
    const data = await res.json();
    // handle success
  } catch (error) {
    setError("Network error");
    addToast("Network error", "error");
  }
};
```

**After:**
```tsx
const { execute, loading, error } = useApi({
  showToastOnError: true,
  successMessage: "Operation successful"
});

const handleSubmit = async () => {
  await execute("/api/endpoint");
};
```

### From Basic Error Boundary

**Before:**
```tsx
<ErrorBoundary>
  <Component />
</ErrorBoundary>
```

**After:**
```tsx
<ErrorBoundary
  showReportButton
  onError={(error, info) => {
    // Custom error handling
    analytics.track("error", { error: error.message });
  }}
>
  <Component />
</ErrorBoundary>
```

## Error Reporting Integration

The system is designed to integrate with error reporting services:

### Sentry Integration
```tsx
// In ErrorBoundary.tsx
import * as Sentry from "@sentry/nextjs";

componentDidCatch(error: Error, info: ErrorInfo) {
  Sentry.captureException(error, { extra: info });
}
```

### LogRocket Integration
```tsx
// In globalErrorHandler.ts
import LogRocket from "logrocket";

reportError(error: Error, context?: Record<string, any>) {
  LogRocket.captureException(error, { extra: context });
}
```

## Best Practices

1. **Use Custom Hooks**: Prefer `useApi` and `useApiMutation` for all API calls
2. **Wrap Components**: Use `ErrorBoundary` around feature components
3. **Handle Errors Gracefully**: Always provide fallbacks for error states
4. **User Feedback**: Use toasts for user-facing errors, console for debugging
5. **Error Context**: Include relevant context when reporting errors
6. **Test Error States**: Ensure error boundaries and handlers work correctly

## Error Types

- **API Errors**: Network issues, server errors, validation errors
- **Component Errors**: React rendering errors, prop validation failures
- **Global Errors**: Unhandled promises, uncaught exceptions
- **User Errors**: Validation failures, permission issues

## Monitoring

Monitor error rates and types through:
- Browser console logs
- Error reporting service dashboards
- Application performance monitoring
- User feedback and support tickets