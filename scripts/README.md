# Port Configuration Script

Automated port management system to avoid conflicts between Docker-based applications.

## Overview

The `generate_ports.py` script automatically:
- Finds available ports on your system using socket testing
- Generates random ports in safe ranges (15000-16999) to avoid common conflicts
- Updates `.env` file with new port assignments
- Preserves existing non-port environment variables
- Auto-detects project name from `docker-compose.yml`

## Quick Start

```bash
# Generate new ports (preserves other .env variables)
python scripts/generate_ports.py

# See what would be generated without modifying .env
python scripts/generate_ports.py --dry-run

# Regenerate entire .env file from scratch
python scripts/generate_ports.py --fresh

# After generating ports, restart Docker containers
docker compose down && docker compose up -d
```

## Using This as a Template for New Projects

When creating a new project from this template, follow these steps:

### 1. Customize Port Configuration

Edit `scripts/generate_ports.py` and modify the `PORT_CONFIG` dictionary (lines 20-38):

```python
PORT_CONFIG = {
    # Format: 'ENV_VAR_NAME': (min_port, max_port, preferred_port, 'Description')
    # preferred_port=None means always generate random port in range

    # Example: Add your own services
    'POSTGRES_MAIN_PORT': (15000, 15999, None, 'PostgreSQL Main Database'),
    'REDIS_CACHE_PORT': (16000, 16999, None, 'Redis Cache'),
    'BACKEND_PORT': (8000, 9000, 8000, 'Backend API Server'),
}
```

**Configuration Format:**
- `ENV_VAR_NAME`: The environment variable name (must match usage in `docker-compose.yml` and code)
- `min_port`: Minimum port in range
- `max_port`: Maximum port in range
- `preferred_port`: Try this port first (use `None` to always randomize)
- `Description`: Human-readable description (first word is used for grouping)

### 2. Update docker-compose.yml

Ensure your `docker-compose.yml` uses the environment variables:

```yaml
services:
  db:
    ports:
      - "127.0.0.1:${POSTGRES_MAIN_PORT:-5432}:5432"

  redis:
    ports:
      - "127.0.0.1:${REDIS_CACHE_PORT:-6379}:6379"
```

**Format:** `${ENV_VAR:-default_value}`

### 3. Update Application Settings

Make sure your application reads ports from environment variables:

**Python (Pydantic Settings):**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_MAIN_PORT: int = 5432
    REDIS_CACHE_PORT: int = 6379

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )
```

**Other Languages:**
- Use environment variable libraries that support `.env` files
- Examples: `python-dotenv`, `godotenv` (Go), `dotenv` (Node.js)

### 4. Set Project Name (Optional)

The script auto-detects your project name from `docker-compose.yml`. To override:

Edit `scripts/generate_ports.py` line 41:

```python
PROJECT_NAME: Optional[str] = "My Custom Project Name"
```

### 5. Generate Initial Ports

```bash
# Generate ports for the first time
python scripts/generate_ports.py

# Review the generated .env file
cat .env

# Start your services
docker compose up -d
```

## Port Range Recommendations

Use high port ranges to avoid conflicts with standard services:

| Range | Purpose | Standard Conflicts Avoided |
|-------|---------|---------------------------|
| 15000-15999 | Database ports | PostgreSQL (5432), MySQL (3306) |
| 16000-16999 | Cache/Session stores | Redis (6379), Memcached (11211) |
| 17000-17999 | Message queues | RabbitMQ (5672), Kafka (9092) |
| 18000-18999 | Search/Analytics | Elasticsearch (9200), Kibana (5601) |
| 8000-9000 | Backend APIs | Development servers |
| 5000-6000 | Frontend | React (3000), Vue (5173) |

## Command-Line Options

```bash
python scripts/generate_ports.py [OPTIONS]

Options:
  --dry-run    Show what would be generated without modifying .env
  --fresh      Overwrite entire .env file (don't preserve existing variables)
  --help       Show help message
```

## How It Works

### 1. Port Availability Check

The script uses socket binding to verify port availability:

```python
def is_port_available(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False
```

### 2. Random Port Generation

For each service:
1. If a preferred port is specified and available, use it
2. Otherwise, generate random ports in the configured range
3. Test each port before assignment (max 100 attempts)

### 3. .env File Update

The script:
1. Parses existing `.env` file
2. Preserves all non-port variables (unless `--fresh` is used)
3. Organizes ports by category
4. Adds timestamp and project name
5. Writes formatted `.env` file

### 4. Project Name Detection

Automatically detects project name by:
1. Checking `PROJECT_NAME` variable in script
2. Reading first `container_name` from `docker-compose.yml`
3. Cleaning suffixes (`_db`, `_redis`, etc.)
4. Falling back to "Application" if not found

## Examples

### Example 1: Microservices Project

```python
PORT_CONFIG = {
    # API Services
    'AUTH_SERVICE_PORT': (8100, 8199, 8100, 'Authentication Service'),
    'USER_SERVICE_PORT': (8200, 8299, 8200, 'User Service'),
    'ORDER_SERVICE_PORT': (8300, 8399, 8300, 'Order Service'),

    # Databases (one per service)
    'AUTH_DB_PORT': (15100, 15199, None, 'Authentication Database'),
    'USER_DB_PORT': (15200, 15299, None, 'User Database'),
    'ORDER_DB_PORT': (15300, 15399, None, 'Order Database'),

    # Shared infrastructure
    'REDIS_CACHE_PORT': (16000, 16099, None, 'Redis Cache'),
    'MESSAGE_QUEUE_PORT': (17000, 17099, None, 'Message Queue'),
}
```

### Example 2: Simple Full-Stack App

```python
PORT_CONFIG = {
    'POSTGRES_PORT': (15000, 15999, None, 'PostgreSQL Database'),
    'REDIS_PORT': (16000, 16999, None, 'Redis Cache'),
    'BACKEND_PORT': (8000, 9000, 8000, 'Backend API'),
    'FRONTEND_PORT': (5000, 6000, 5173, 'Frontend Dev Server'),
}
```

### Example 3: Development Environment with Multiple Stacks

```python
PORT_CONFIG = {
    # Web stack
    'WEB_DB_PORT': (15000, 15099, None, 'Web PostgreSQL'),
    'WEB_REDIS_PORT': (16000, 16099, None, 'Web Redis'),

    # Analytics stack
    'ANALYTICS_DB_PORT': (15100, 15199, None, 'Analytics PostgreSQL'),
    'ELASTICSEARCH_PORT': (18000, 18099, None, 'Elasticsearch'),

    # Applications
    'WEB_BACKEND_PORT': (8000, 8099, 8000, 'Web Backend'),
    'ANALYTICS_BACKEND_PORT': (8100, 8199, 8100, 'Analytics Backend'),
}
```

## Troubleshooting

### "Could not find available port in range"

**Cause:** All ports in the specified range are in use

**Solutions:**
1. Expand the port range in `PORT_CONFIG`
2. Stop unused Docker containers: `docker ps -a` then `docker stop <container>`
3. Check what's using ports: `ss -tuln | grep :<port>`

### Ports still conflict after running script

**Cause:** Docker containers weren't restarted

**Solution:**
```bash
docker compose down
docker compose up -d
```

### .env variables are being overwritten

**Cause:** Using `--fresh` flag or variables are named like port variables

**Solutions:**
1. Don't use `--fresh` flag (default preserves variables)
2. Rename variables that match `PORT_CONFIG` keys
3. Add them back to `PORT_CONFIG` if they are port-related

### Project name is wrong

**Solution:** Set `PROJECT_NAME` in `scripts/generate_ports.py`:
```python
PROJECT_NAME: Optional[str] = "Your Project Name"
```

## Integration with CI/CD

### GitHub Actions

```yaml
- name: Generate available ports
  run: python scripts/generate_ports.py

- name: Start services
  run: docker compose up -d

- name: Run tests
  run: pytest
```

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Ensure ports are available before commit
python scripts/generate_ports.py --dry-run
```

## Advanced Usage

### Custom Port Assignment Logic

Modify `generate_ports()` function to add custom logic:

```python
def generate_ports() -> Dict[str, int]:
    ports = {}

    for env_var, (min_port, max_port, preferred, description) in PORT_CONFIG.items():
        # Custom logic example: Use sequential ports for databases
        if 'DB' in env_var:
            ports[env_var] = find_sequential_port(min_port, ports.values())
        else:
            # Default random logic
            if preferred and is_port_available(preferred):
                ports[env_var] = preferred
            else:
                ports[env_var] = find_available_port(min_port, max_port)

    return ports
```

### Environment-Specific Configuration

Create different configurations for dev/staging/prod:

```python
import os

ENV = os.getenv('ENVIRONMENT', 'development')

if ENV == 'production':
    PORT_CONFIG = {
        # Use standard ports in production
        'POSTGRES_PORT': (5432, 5432, 5432, 'PostgreSQL Database'),
        'REDIS_PORT': (6379, 6379, 6379, 'Redis Cache'),
    }
else:
    PORT_CONFIG = {
        # Use high ports in development
        'POSTGRES_PORT': (15000, 15999, None, 'PostgreSQL Database'),
        'REDIS_PORT': (16000, 16999, None, 'Redis Cache'),
    }
```

## License

This script is part of the project template and can be freely used and modified.
