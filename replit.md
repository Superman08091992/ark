# Project Ark

## Overview
Project Ark is a modular local-first AI stack featuring Kyle (an AI agent), Express backend, and Ollama-powered LLM capabilities. The project provides a web interface for chatting with the Kyle agent.

## Project Structure
- **agents/kyle/** - Kyle AI agent implementation
- **services/core/** - Main Express server serving UI and API
- **apps/core/** - Alternative core service
- **apps/gui/** - GUI service
- **packages/shared-node/** - Shared Node.js utilities
- **ui/** - Frontend UI (HTML, CSS, JS)

## Tech Stack
- Node.js 20
- Express.js
- pnpm (workspace monorepo)
- node-fetch for API calls

## Development
The main server runs on port 5000 and serves both the UI and API endpoints:
- `/` - Main UI
- `/health` - Health check endpoint
- `/version` - Version information
- `/chat` - Chat with Kyle agent
- `/memory` - View conversation memory
- `/memory/reset` - Clear conversation memory

## Environment Variables
- `OPENAI_BASE_URL` - Base URL for LLM API (required for Kyle agent)
- `OPENAI_MODEL` - Model name (defaults to "tinyllama")
- `PORT` - Server port (defaults to 5000)

## Recent Changes
- 2025-10-03: Set up for Replit environment
  - Configured server to run on port 5000 with 0.0.0.0 host
  - Created package.json files for services/core and agents/kyle
  - Updated pnpm workspace configuration
  - Created memory directory for conversation storage
  - Configured deployment for autoscale
