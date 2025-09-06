# ChainSync

![ChainSync Logo](./docs/screenshot.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org/)

**Agentic AI + RAG for load planning and route optimization for logistics/supply chain**

ChainSync is a production-quality, local-first monorepo that provides intelligent route optimization and load planning for logistics operations. Built with modern technologies and designed to run entirely offline with optional cloud integrations.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ 
- Python 3.11+
- pnpm 8+

### One-Click Local Setup

```bash
# Clone the repository
git clone https://github.com/your-org/chainsync.git
cd chainsync

# Install dependencies
pnpm install

# Set up environment files
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env

# Start all services
pnpm dev
```

The application will be available at:
- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🏗️ Architecture

ChainSync follows hexagonal (ports & adapters) architecture with clear bounded contexts:

- **Orders**: Order management and validation
- **Packing/LoadPlanner**: Bin-packing and loading sequence optimization  
- **Routing**: Vehicle routing with time windows using OR-Tools
- **Knowledge/RAG**: Local vector database with FAISS for document retrieval
- **Telemetry**: Event tracking and analytics

### Tech Stack

**Frontend** (`apps/web`)
- Next.js 14 with App Router
- TypeScript, Tailwind CSS, shadcn/ui
- TanStack Query, Zustand, Zod
- MapLibre GL (no API keys required)

**Backend** (`apps/api`)  
- FastAPI with Pydantic v2
- SQLAlchemy 2.0 + Alembic
- SQLite (local) with optional AWS adapters

**AI/Optimization** (`packages/ai`)
- sentence-transformers (MiniLM)
- FAISS vector store
- OR-Tools for vehicle routing
- Deterministic seeded sample data

**Shared** (`packages/core`)
- Shared TypeScript types and Zod schemas
- OpenAPI client generation
- Design tokens and utilities

## 📊 Features

### Core Capabilities
- **CSV Order Upload**: Bulk import orders with validation
- **Route Optimization**: Multi-vehicle routing with time windows
- **Load Planning**: Bin-packing with accessibility-first loading
- **RAG Knowledge Base**: Query local documents for logistics insights
- **Interactive Dashboard**: KPIs, route visualization, and analytics

### UI/UX
- Modern dark-themed dashboard
- Responsive design with keyboard shortcuts
- Real-time route visualization with MapLibre
- Print-friendly loading checklists
- Empty state illustrations

## 🛠️ Development

### Commands

```bash
# Development
pnpm dev              # Start all services in development mode
pnpm build            # Build all packages and apps
pnpm test             # Run all tests
pnpm lint             # Lint all code
pnpm typecheck        # Type check TypeScript

# Screenshots
pnpm screenshot       # Generate UI screenshot for README
```

### Project Structure

```
chainsync/
├── apps/
│   ├── web/          # Next.js 14 frontend
│   └── api/          # FastAPI backend
├── packages/
│   ├── core/         # Shared types, schemas, OpenAPI client
│   └── ai/           # RAG + OR-Tools optimization
├── docs/             # Architecture docs and ADRs
├── tools/            # Development tools and scripts
└── data/             # Local SQLite database and vector store
```

## 🏃‍♂️ Running Services

### Development Mode
```bash
pnpm dev
```

### Production Mode
```bash
pnpm build
pnpm start
```

### Docker (Local Only)
```bash
docker-compose up --build
```

## 🧪 Testing

```bash
# Unit tests
pnpm test

# Integration tests  
pnpm test:integration

# E2E tests with Playwright
pnpm test:e2e
```

## 📚 Documentation

- [Architecture Overview](./docs/architecture.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Contributing Guidelines](./CONTRIBUTING.md)
- [Code of Conduct](./CODE_OF_CONDUCT.md)

## 🔧 Configuration

### Local-First Design

ChainSync runs entirely locally by default:
- SQLite database (`./data/chainsync.db`)
- FAISS vector store (`./data/vector_store/`)
- No external API calls or cloud dependencies

### Optional Cloud Integration

AWS adapters are provided but **disabled by default**. To enable cloud features:

1. Uncomment AWS configuration in `.env` files
2. Set `USE_AWS_ADAPTERS=true`
3. Configure AWS credentials and resources

**Available AWS integrations** (optional):
- S3 for document storage
- SQS/SNS for event messaging  
- CloudWatch for observability

## 🎯 Customization

### Replace the Logo

Drop your logo as `chainsync-logo.png` in the repository root - it will automatically be copied to `/public/assets/logo.png` and appear in the app header.

### Environment Variables

See `.env.example` files in `apps/web/` and `apps/api/` for all configuration options.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 🔒 Security

For security concerns, please see our [SECURITY.md](SECURITY.md) policy.

---

**ChainSync** - Intelligent logistics optimization, running locally first. 🚛✨