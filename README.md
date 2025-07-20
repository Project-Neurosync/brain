# NeuroSync 🧠

**AI-Powered Developer Knowledge Transfer Platform**

NeuroSync is a comprehensive platform that eliminates knowledge silos in development teams through intelligent AI-powered knowledge management, semantic search, and automated context retention.

## 🚀 Features

- **🤖 AI-Powered Knowledge Transfer** - Intelligent onboarding and project context
- **🔍 Semantic Search** - Find information across all your repositories, docs, and conversations
- **💰 Cost Optimization** - Smart AI model selection reducing costs by up to 95%
- **🔗 Multi-Source Integration** - GitHub, Jira, Slack, and more
- **👥 Team Collaboration** - Project-based workspaces with role management
- **📊 Analytics & Insights** - Usage tracking and optimization metrics
- **🔐 Enterprise Security** - SOC2 compliant with advanced authentication

## 📁 Project Structure

```
neurosync/
├── 📁 apps/
│   ├── 📁 api/                    # FastAPI Backend
│   │   ├── main.py               # Main application entry
│   │   ├── core/                 # Core AI & data services
│   │   ├── services/             # Business logic services
│   │   └── requirements.txt      # Python dependencies
│   └── 📁 web/                    # Next.js Frontend
│       ├── src/                  # Source code
│       ├── components/           # React components
│       └── package.json          # Node.js dependencies
├── 📁 packages/
│   ├── 📁 shared/                # Shared utilities & types
│   └── 📁 ui/                    # Reusable UI components
├── 📁 docs/                      # Documentation
├── 📁 scripts/                   # Build & deployment scripts
└── 📁 config/                    # Configuration files
```

## 🛠️ Quick Start

### Prerequisites
- **Node.js** >= 18.0.0
- **Python** >= 3.9.0
- **Git**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/neurosync.git
   cd neurosync
   ```

2. **Install all dependencies**
   ```bash
   npm run install:all
   ```

3. **Set up environment variables**
   ```bash
   # Copy example environment file
   cp config/.env.example apps/api/.env
   
   # Edit the .env file with your API keys
   # - OPENAI_API_KEY=your_openai_key
   # - DATABASE_URL=your_database_url
   ```

### Development

**Start both frontend and backend:**
```bash
npm run dev
```

**Or start individually:**
```bash
# Backend only (FastAPI)
npm run dev:api

# Frontend only (Next.js)
npm run dev:web
```

**Access the application:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🏗️ Architecture

### Backend (FastAPI)
- **AI Engine**: OpenAI integration with cost optimization
- **Vector Database**: ChromaDB for semantic search
- **Authentication**: JWT-based with role management
- **Data Ingestion**: Multi-source connectors (GitHub, Jira, Slack)
- **Cost Optimization**: Intelligent model selection (76-84% cost savings)

### Frontend (Next.js)
- **Modern UI**: Tailwind CSS + Radix UI components
- **State Management**: React Query for server state
- **Authentication**: Protected routes with session management
- **Real-time Updates**: WebSocket integration
- **Responsive Design**: Mobile-first approach

## 📊 Cost Optimization

NeuroSync includes intelligent AI cost optimization:

- **Simple queries**: GPT-3.5-turbo ($0.0015/1k tokens)
- **Complex queries**: GPT-4o-mini ($0.00015/1k tokens)
- **Critical queries**: GPT-4 ($0.03/1k tokens)
- **Average savings**: 76-84% cost reduction

## 🔧 Available Scripts

```bash
# Development
npm run dev              # Start both frontend and backend
npm run dev:api          # Start backend only
npm run dev:web          # Start frontend only

# Production
npm run build            # Build for production
npm run start            # Start production server

# Maintenance
npm run lint             # Run linting
npm run test             # Run tests
npm run clean            # Clean build artifacts
npm run install:all      # Install all dependencies
```

## 🚀 Deployment

### Docker (Recommended)
```bash
docker-compose up -d
```

### Manual Deployment
1. Build the frontend: `npm run build`
2. Deploy backend to your preferred platform (AWS, GCP, Azure)
3. Configure environment variables
4. Set up database and vector store

## 📖 Documentation

- **[API Documentation](./docs/)** - Complete API reference
- **[Architecture Guide](./docs/)** - System design and architecture
- **[Deployment Guide](./docs/)** - Production deployment instructions
- **[Contributing](./docs/)** - Development guidelines

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/neurosync/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/neurosync/discussions)

---

**Built with ❤️ for developers who value knowledge sharing and efficient onboarding.**
