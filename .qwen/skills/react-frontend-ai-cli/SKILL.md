# Procedure: React Frontend Development for AI-CLI

## Overview
This skill captures the approach for building a React-based frontend for the AI-CLI tool using Vite as the build system.

## Key Components

### 1. Project Setup
- **Framework**: React 18 for UI framework
- **Build Tool**: Vite 8.2.2 for frontend bundling
- **Package Manager**: npm
- **CSS Framework**: Bootstrap 5.3 for component styling

### 2. Component Architecture
Each functional component follows the same pattern:
```jsx
import { useState } from 'react';

function ComponentName() {
  // State management using useState hooks
  // Backend API integration using fetch
  // Bootstrap styling with className attributes
  // Error handling with try/catch
}

export default ComponentName;
```

### 3. Component Types
- **DocumentEditor**: File upload, preview, and download
- **SummaryTool**: Document summarization interface
- **TranslateTool**: Text translation with language selection
- **ExtractTool**: Entity/dates/numbers extraction
- **Settings**: Backend and AI configuration management

### 4. Main Application Layout
- **Header**: Application title and description
- **Navigation**: Tab-based navigation between components
- **Main Content**: Dynamic content area showing active component
- **Footer**: Version and server information

### 5. Tab Navigation Pattern
```jsx
const [activeTab, setActiveTab] = useState('documents');
const tabs = [
  { id: 'documents', label: 'Documentos', icon: '📄' },
  { id: 'summary', label: 'Resumir', icon: '📊' },
  { id: 'translate', label: 'Traducir', icon: '🌐' },
  { id: 'extract', label: 'Extraer', icon: '🔍' },
  { id: 'settings', label: 'Configuración', icon: '⚙️' },
];

// Conditional rendering in main content area
{activeTab === 'documents' && <DocumentEditor />}
{activeTab === 'summary' && <SummaryTool />}
// ... etc
```

### 6. Backend Integration Pattern
```jsx
const handleAction = async () => {
  setLoading(true);
  try {
    const response = await fetch(`${backendUrl}/endpoint`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ /* payload */ })
    });
    const data = await response.json();
    // Update UI with response
  } catch (error) {
    // Error handling
  } finally {
    setLoading(false);
  }
};
```

### 7. Bootstrap Component Usage
```jsx
<input className="form-control" />
<select className="select" />
<textarea className="textarea" />
<button className="btn btn-primary" />
<button className="btn btn-secondary" />
```

## Tooling

- **React**: 18 (functional components, hooks)
- **Vite**: 8.2.2 (fast HMR, production builds)
- **Bootstrap**: 5.3 (UI components)
- **npm**: Package manager

## Build Commands
- **Development**: `npm run dev` (HMR enabled)
- **Production Build**: `npm run build`
- **Preview**: `npm run preview`

## Styling Approach
- Custom inline styles for layout (flexbox, positioning)
- Bootstrap classes for form controls and buttons
- Consistent color scheme (#217346 for primary, #f5f5f5 for backgrounds)
- Responsive design patterns

## State Management
- **Component-level state**: `useState` hooks for local state
- **No global state**: Each component manages its own state
- **Props for sharing**: Passed between parent-child components

## Error Handling
- Try/catch blocks around async operations
- Loading states for long operations
- User-friendly error messages in Spanish

## Related Skills
- `fastapi-chat-endpoint-llama-cpp`: Backend API endpoints used by frontend
- `python-deps-virtual-env`: Backend server dependencies

## Dependencies

- **React**: `react@18`
- **Vite**: `vite@8.2.2`
- **Bootstrap**: `bootstrap@5.3`
- **npm**: npm package manager

## Notes
- Frontend and backend run on separate ports (frontend: Vite dev server, backend: 3094)
- AI model served via llama.cpp on port 1234
- File storage uses SQLite database in backend
- Document metadata persisted to backend for cross-tab access
