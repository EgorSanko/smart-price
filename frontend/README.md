# Smart Price Frontend

AI-powered метапоиск товаров с интеллектуальным анализом цен.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State Management:** React Query (TanStack Query)
- **Charts:** Recharts
- **Icons:** Lucide React

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running at `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page
│   ├── search/             # Search results page
│   ├── product/[id]/       # Product detail page
│   ├── compare/            # Price comparison page
│   └── chat/               # AI assistant page
├── components/             # React components
│   ├── layout/             # Header, Footer
│   ├── search/             # SearchBar, FilterPanel
│   └── product/            # ProductCard, PriceChart
├── hooks/                  # Custom React hooks
│   ├── useSearch.ts        # Search hook
│   └── useProducts.ts      # Products hooks
├── lib/                    # Utilities
│   ├── api.ts              # API client
│   └── utils.ts            # Helper functions
└── types/                  # TypeScript types
    ├── product.ts          # Product types
    └── api.ts              # API types
```

## Available Scripts

```bash
npm run dev        # Start development server
npm run build      # Build for production
npm run start      # Start production server
npm run lint       # Run ESLint
npm run type-check # Run TypeScript type checking
```

## Pages

| Route | Description |
|-------|-------------|
| `/` | Home page with search |
| `/search?q=...` | Search results |
| `/product/[id]` | Product details with price history |
| `/compare` | Price comparison tool |
| `/chat` | AI shopping assistant |

## API Integration

The frontend connects to the backend API at `NEXT_PUBLIC_API_URL` (default: `http://localhost:8000/api/v1`).

### Endpoints Used

- `GET /search` — Search products
- `GET /search/suggest` — Search suggestions
- `GET /products` — List products
- `GET /products/{id}` — Product details with price history
- `GET /products/{id}/similar` — Similar products
- `GET /products/{id}/compare` — Price comparison
- `GET /analytics/forecast/{id}` — Price forecast

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000/api/v1` |

## Development

### Code Style

- Use TypeScript strict mode
- Follow component naming conventions (PascalCase)
- Use `cn()` helper for conditional classes
- Prefer `async/await` over `.then()`

### Adding Components

1. Create component in appropriate folder under `src/components/`
2. Export from folder's `index.ts`
3. Import via `@/components`

### Adding Pages

1. Create page in `src/app/[route]/page.tsx`
2. Use Server Components by default
3. Add `'use client'` directive only when needed

## Build & Deploy

```bash
# Build production bundle
npm run build

# Start production server
npm run start
```

For Docker deployment, use the Dockerfile provided.
