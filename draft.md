# Prompt: Create Logistics System UI with React, Vite, Shadcn UI, and TypeScript

## Context

You are tasked with creating a modern frontend UI for a Logistics System backend that handles load parsing, driver management, and trip planning. The backend is built with FastAPI and provides RESTful endpoints for managing loads, drivers, and notifications. You need to create a React application that interfaces with this backend, providing an intuitive and responsive user experience.

## Backend System Overview

The backend system provides these key functionalities:
- Text parsing of load information into structured data
- Storage of load and leg information in a PostgreSQL database
- Driver management and load assignment
- Telegram notification integration for drivers
- RESTful API endpoints

The core entities in the system are:
- Loads (trips with legs, pickup/dropoff locations, timing, rates)
- Drivers
- Facilities (pickup and dropoff locations)
- Companies

## Tech Stack Requirements

Create a UI application using:
- **React 18** with TypeScript
- **Vite** as the build tool
- **Shadcn UI** for component library
- **TanStack Query** for API data fetching
- **React Router** or **TanStack Router** for routing
- **Tailwind CSS** for styling
- **Axios** for API requests
- **Zod** for schema validation
- **Zustand** for state management (if needed)

## API Endpoints to Integrate

Based on the backend, implement UI components that integrate with these endpoints:

```
GET /loads/ - Get all loads with pagination
POST /loads/parse - Parse load text
POST /loads/create - Create a new load
GET /loads/{load_id} - Get a specific load

PUT /load-management/{load_id}/assign-driver/{driver_id} - Assign driver to load
GET /load-management/assigned-drivers - Get drivers with assignments
GET /load-management/available-drivers - Get available drivers 
POST /load-management/{load_id}/notify-driver - Send notification to driver

GET / - Root endpoint (API info)
GET /health - Health check endpoint
```

## Required UI Features

Create a comprehensive UI with these features:

1. **Dashboard Page**
   - Overview statistics (total loads, assigned loads, available drivers)
   - Recent activity feed
   - Quick access buttons to key functions

2. **Load Management Pages**
   - Load listing page with filtering and pagination
   - Load detail view showing all load information and legs
   - Load creation page with text parsing capability
   - Load assignment interface

3. **Driver Management Pages**
   - Driver listing page (showing available and assigned drivers)
   - Driver detail view
   - Driver assignment interface

4. **Notification Interface**
   - Form to send notifications to drivers
   - Notification history view

## Specific Component Implementation Details

Implement the following key components:

### 1. Load Text Parser Component

Create a component that allows users to:
- Paste load text in a text area
- Parse the text by calling the parsing API
- Preview the parsed data before saving
- Save the parsed data to create a new load

Example request format for parsing:
```
POST /loads/parse
Content-Type: text/plain

T-115CSXYJM

Spot

1

DCA2 Eastvale, California 91752

Sun, May 18, 05:28 PDT

3

SBD1 Bloomington, CA 92316

Sun, May 18, 15:38 PDT
342 mi

10h 41m
53' Trailer

P

Drop/Live

$1 019,44

$2.98/mi

P. Sementeyev
```

### 2. Load Listing Component

Create a table component that:
- Displays loads with pagination
- Shows key load information (ID, pickup/dropoff locations, times, rate, driver)
- Includes filters for trip ID, locations, and date ranges
- Provides actions for viewing details, assigning drivers, and sending notifications

### 3. Load Detail View

Create a detailed view that:
- Shows all load information
- Displays legs in an expandable format
- Includes driver assignment section
- Shows a timeline visualization of the load journey

### 4. Driver Management Interface

Create components for:
- Listing drivers with their status (available/assigned)
- Assigning drivers to loads
- Viewing driver details and assignment history

### 5. Notification Component

Create a component that:
- Allows sending notifications to drivers about loads
- Shows notification history and status

## Data Models

Implement TypeScript interfaces for these models based on the backend schemas:

```typescript
// Load model
interface Load {
  id: number;
  trip_id: string;
  pickup_facility?: string;
  dropoff_facility?: string;
  pickup_address?: string;
  dropoff_address?: string;
  start_time: string; // ISO date string
  end_time: string; // ISO date string
  rate: number;
  rate_per_mile: number;
  distance?: number;
  assigned_driver?: string;
  legs: Leg[];
}

// Leg model
interface Leg {
  id: number;
  leg_id: string;
  pickup_facility_id: string;
  dropoff_facility_id: string;
  pickup_address: string;
  dropoff_address: string;
  pickup_time: string; // ISO date string
  dropoff_time: string; // ISO date string
  fuel_sur_charge: number;
  distance?: number;
  assigned_driver?: string;
}

// Driver model
interface Driver {
  id: number;
  name: string;
  company_id: number;
  chat_id?: number;
}
```

## Project Structure

Set up the project with this recommended structure:

```
src/
├── components/          # Reusable components
│   ├── ui/             # Shadcn UI components
│   ├── loads/          # Load-specific components
│   ├── drivers/        # Driver-specific components
│   └── common/         # Shared components
├── pages/              # Application pages
│   ├── Dashboard/
│   ├── Loads/
│   ├── LoadDetail/
│   ├── CreateLoad/
│   ├── Drivers/
│   └── Notifications/
├── hooks/              # Custom React hooks
│   ├── useLoads.ts
│   ├── useDrivers.ts
│   └── useNotifications.ts
├── api/                # API integration
│   ├── client.ts       # Axios instance
│   ├── loads.ts        # Load-related API calls
│   ├── drivers.ts      # Driver-related API calls
│   └── notifications.ts
├── types/              # TypeScript types
├── utils/              # Utility functions
├── store/              # State management
└── lib/                # Configurations
```

## Implementation Steps

1. Set up a new Vite project with React and TypeScript
2. Configure Tailwind CSS and Shadcn UI
3. Set up routing with React Router or TanStack Router
4. Create API integration layer with Axios
5. Implement data fetching with TanStack Query
6. Create UI components for each feature
7. Implement pages that use these components
8. Add state management where needed
9. Style the application with Tailwind CSS

## Example Component: Load Parser

```tsx
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { parseLoad, createLoad } from '@/api/loads';
import { useMutation } from '@tanstack/react-query';

export function LoadParser() {
  const [loadText, setLoadText] = useState('');
  const [parsedData, setParsedData] = useState(null);
  
  const parseMutation = useMutation({
    mutationFn: parseLoad,
    onSuccess: (data) => {
      setParsedData(data);
    },
  });
  
  const createMutation = useMutation({
    mutationFn: createLoad,
    onSuccess: (data) => {
      // Handle success (e.g., redirect to load detail)
    },
  });
  
  const handleParse = () => {
    parseMutation.mutate(loadText);
  };
  
  const handleCreate = () => {
    createMutation.mutate(loadText);
  };
  
  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle>Parse Load Information</CardTitle>
      </CardHeader>
      <CardContent>
        <Textarea 
          value={loadText}
          onChange={(e) => setLoadText(e.target.value)}
          placeholder="Paste load text here..."
          className="min-h-[200px]"
        />
        
        {parsedData && (
          <div className="mt-4 p-4 border rounded-md">
            <h3 className="font-medium">Parsed Load Data:</h3>
            <pre className="mt-2 text-sm bg-gray-100 p-2 rounded overflow-auto">
              {JSON.stringify(parsedData, null, 2)}
            </pre>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button 
          onClick={handleParse}
          disabled={!loadText || parseMutation.isPending}
        >
          {parseMutation.isPending ? 'Parsing...' : 'Parse Load Text'}
        </Button>
        
        <Button 
          onClick={handleCreate}
          disabled={!loadText || createMutation.isPending}
          variant="default"
        >
          {createMutation.isPending ? 'Creating...' : 'Create Load'}
        </Button>
      </CardFooter>
    </Card>
  );
}
```

## Example API Integration for Loads

```typescript
// api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;

// api/loads.ts
import apiClient from './client';
import type { Load } from '@/types';

export async function getLoads(params?: { skip?: number; limit?: number }) {
  const response = await apiClient.get<Load[]>('/loads/', { params });
  return response.data;
}

export async function getLoad(id: number) {
  const response = await apiClient.get<Load>(`/loads/${id}`);
  return response.data;
}

export async function parseLoad(text: string) {
  const response = await apiClient.post('/loads/parse', text, {
    headers: {
      'Content-Type': 'text/plain',
    },
  });
  return response.data;
}

export async function createLoad(text: string) {
  const response = await apiClient.post('/loads/create', text, {
    headers: {
      'Content-Type': 'text/plain',
    },
  });
  return response.data;
}
```

## Deliverables

Your task is to create:

1. Complete source code for the Logistics System UI
2. A well-structured React application that interfaces with the backend
3. Components for all the required functionality
4. TypeScript types for all data models
5. Proper API integration with error handling
6. Responsive UI using Shadcn UI and Tailwind CSS
7. Clean, maintainable code with proper documentation

## Notes on Backend Connection

- The backend runs on port 8000 by default
- Communication is via HTTP RESTful API
- Some endpoints expect content-type: text/plain
- Error handling should account for various HTTP status codes

Create a user-friendly, intuitive interface that makes it easy for logistics operators to manage loads, drivers, and notifications efficiently.