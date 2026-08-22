# Future Oracle Frontend

A React + TypeScript frontend for exploring job market data and weekly skill indicators.

## Technology Stack

- React 18
- TypeScript
- Vite
- Native fetch API for backend communication
- No UI framework dependencies (clean, minimal styling)

## Project Structure

```
src/
├── api/           # API client for backend communication
├── components/    # Reusable UI components
├── pages/         # Main application pages
├── types/         # TypeScript type definitions
├── App.tsx        # Main application component
└── main.tsx       # Application entry point
```

## Features

### Jobs Page
- Search jobs by title and description text
- Filter by source, skill, location, remote status
- Filter by publication date range
- Job cards showing:
  - Title (linked to original source)
  - Company name
  - Source information
  - Publication date
  - Location and remote status
  - Employment type and category
  - Matched skills (as tags)
  - Description preview

### Weekly Indicators Page
- Filter by source and skill
- Filter by period range
- Table showing:
  - Week range
  - Source and skill information
  - Skill share percentage (converted from backend decimal)
  - Eligible and matching posting counts
  - Coverage days
  - Data quality indicators

### Data Quality Validation
- Highlights indicators with insufficient data
- Uses MVP rules: ≥30 eligible postings and ≥5 coverage days
- Visual indicators for invalid data with explanatory text

## Development

### Setup
```bash
cd frontend
npm install
```

### Development Server
```bash
npm run dev
```

### Build
```bash
npm run build
```

### Type Checking
```bash
npx tsc --noEmit
```

## Configuration

Set the backend API URL in `.env`:
```
VITE_API_BASE_URL=http://localhost:8000
```

## API Integration

The frontend connects to these backend endpoints:

- `GET /api/jobs` - Job listings with filters
- `GET /api/indicators/weekly` - Weekly skill indicators
- `GET /api/sources` - Available data sources
- `GET /api/skills` - Available skills

All API responses use the exact schemas defined by the backend without modifications.

## MVP Constraints

This implementation follows strict MVP guidelines:
- No authentication system
- No predictions or AI features
- No backend modifications
- No fake/mock data
- Simple, professional UI without complex animations
- Client-side only (no server-side routing)
- Uses native browser APIs where possible