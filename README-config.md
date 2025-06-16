# Configuration Guide

## Environment Files

This project now uses environment variables for configuration instead of YAML files.

### Available Environment Files:

- `.env.example` - Template showing all available variables
- `.env.local` - Local development environment with actual values
- `.env.integration` - Integration environment configuration

### How to Use:

1. **For local development:**
   ```bash
   cp .env.local .env
   # or
   uv run --env-file .env.local python main.py
   ```

2. **For integration environment:**
   ```bash
   cp .env.integration .env
   # or
   uv run --env-file .env.integration python main.py
   ```

3. **For production:**
   Set environment variables directly in your deployment system.

### Security Notes:

- Never commit `.env` files to git
- The `.env.local` and `.env.integration` files contain actual credentials and should be treated carefully
- For production, use proper secret management systems

### Migration from YAML:

The old YAML configuration files are now deprecated. All values have been migrated to the environment files above.