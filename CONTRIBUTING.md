# Contributing to ChainSync

We love your input! We want to make contributing to ChainSync as easy and transparent as possible.

## Development Process

1. Fork the repo and create your branch from `main`
2. Make your changes following our coding standards
3. Add tests for any new functionality
4. Ensure all tests pass
5. Update documentation as needed
6. Submit a pull request

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- pnpm 8+

### Setup

```bash
# Clone your fork
git clone https://github.com/your-username/chainsync.git
cd chainsync

# Install dependencies
pnpm install

# Set up environment
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env

# Start development
pnpm dev
```

## Code Style

### TypeScript/JavaScript
- Use TypeScript for type safety
- Follow ESLint configuration
- Use Prettier for formatting
- Prefer functional components in React

### Python
- Follow PEP 8 style guide
- Use type hints where possible
- Use ruff for linting
- Use mypy for type checking

### Commit Messages
Use conventional commits format:
```
feat: add new route optimization algorithm
fix: resolve issue with CSV upload validation
docs: update API documentation
```

## Testing

### Frontend
```bash
# Unit tests
pnpm test

# E2E tests
pnpm test:e2e
```

### Backend
```bash
# Unit tests
cd apps/api
pytest

# Integration tests
pytest tests/integration/
```

## Architecture Guidelines

### Frontend
- Use App Router for Next.js 14
- Implement proper error boundaries
- Use React Query for server state
- Follow atomic design principles

### Backend
- Follow hexagonal architecture
- Use dependency injection
- Implement proper error handling
- Write unit tests for domain logic

### Shared
- Keep packages focused and minimal
- Use proper TypeScript types
- Follow semver for versioning

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Increase version numbers following SemVer
3. Include tests for new functionality
4. Ensure CI passes
5. Request review from maintainers

## Code of Conduct

### Our Pledge
We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards
- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what's best for the community

### Enforcement
Instances of abusive behavior may be reported to the project maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.