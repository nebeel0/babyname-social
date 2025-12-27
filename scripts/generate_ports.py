#!/usr/bin/env python3
"""
Generate random available ports and update .env file.
This helps avoid port conflicts with other applications.

TEMPLATE CONFIGURATION:
When using this project as a template, customize the PORT_CONFIG below
to match your project's services and preferred port ranges.
"""
import socket
import random
import re
from pathlib import Path
from typing import Dict, Tuple, Optional

# ============================================================================
# TEMPLATE CONFIGURATION - Customize this for your project
# ============================================================================

PORT_CONFIG = {
    # Format: 'ENV_VAR_NAME': (min_port, max_port, preferred_port, 'Description')
    # preferred_port=None means always generate random port in range

    # Database ports - use high range to avoid conflicts (15000-15999)
    'POSTGRES_NAMES_PORT': (15000, 15999, None, 'PostgreSQL Names Database'),
    'POSTGRES_USERS_PORT': (15000, 15999, None, 'PostgreSQL Users Database'),

    # Cache/Session ports - use high range (16000-16999)
    'REDIS_CACHE_PORT': (16000, 16999, None, 'Redis Cache'),
    'REDIS_SESSIONS_PORT': (16000, 16999, None, 'Redis Sessions'),

    # Admin tools (15000-15999)
    'PGADMIN_PORT': (15000, 15999, None, 'PgAdmin Web Interface'),

    # Application ports - try standard ports first, fallback to range
    'BACKEND_PORT': (8000, 9000, 8000, 'Backend API Server'),
    'FRONTEND_PORT': (5000, 6000, 5173, 'Frontend Development Server'),
}

# Project name for .env file header (auto-detected from docker-compose.yml if available)
PROJECT_NAME: Optional[str] = None

# ============================================================================
# Core Functions - No need to modify below for template customization
# ============================================================================


def is_port_available(port: int) -> bool:
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False


def find_available_port(start_range: int, end_range: int, max_attempts: int = 100) -> int:
    """Find an available port in the given range."""
    for _ in range(max_attempts):
        port = random.randint(start_range, end_range)
        if is_port_available(port):
            return port
    raise RuntimeError(f"Could not find available port in range {start_range}-{end_range}")


def get_project_name() -> str:
    """Auto-detect project name from docker-compose.yml or use configured name."""
    if PROJECT_NAME:
        return PROJECT_NAME

    # Try to read from docker-compose.yml
    project_root = Path(__file__).parent.parent
    docker_compose = project_root / 'docker-compose.yml'

    if docker_compose.exists():
        content = docker_compose.read_text()
        # Look for common project identifiers in container names
        match = re.search(r'container_name:\s*(\w+)', content)
        if match:
            # Extract base name (remove common suffixes)
            name = match.group(1)
            for suffix in ['_db', '_redis', '_cache', '_sessions', '_pgadmin']:
                name = name.replace(suffix, '')
            return name.replace('_', ' ').title()

    return "Application"


def generate_ports() -> Dict[str, int]:
    """Generate random available ports for all configured services."""
    ports = {}

    for env_var, (min_port, max_port, preferred, description) in PORT_CONFIG.items():
        # Try preferred port first if specified
        if preferred and is_port_available(preferred):
            ports[env_var] = preferred
        else:
            # Generate random port in range
            ports[env_var] = find_available_port(min_port, max_port)

    return ports


def parse_env_file(env_path: Path) -> Dict[str, str]:
    """Parse existing .env file and return non-port variables."""
    if not env_path.exists():
        return {}

    non_port_vars = {}
    content = env_path.read_text()

    for line in content.split('\n'):
        line = line.strip()
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue

        # Parse variable
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            # Keep non-port variables
            if key not in PORT_CONFIG:
                non_port_vars[key] = value.strip()

    return non_port_vars


def update_env_file(ports: Dict[str, int], preserve_vars: bool = True):
    """Update .env file with new ports, optionally preserving other variables."""
    env_path = Path(__file__).parent.parent / '.env'
    project_name = get_project_name()

    # Preserve non-port environment variables
    non_port_vars = parse_env_file(env_path) if preserve_vars else {}

    # Build .env content
    lines = [
        f"# {project_name} - Environment Configuration",
        "# Auto-generated ports to avoid conflicts with other applications",
        f"# Last generated: {__import__('datetime').datetime.now().isoformat()}",
        "",
    ]

    # Group ports by category
    categories = {}
    for env_var, (_, _, _, description) in PORT_CONFIG.items():
        # Extract category from description
        category = description.split()[0]  # e.g., "PostgreSQL", "Redis", "Backend"
        if category not in categories:
            categories[category] = []
        categories[category].append((env_var, ports[env_var], description))

    # Write port sections
    for category, items in categories.items():
        lines.append(f"# {category} Ports")
        for env_var, port, description in items:
            lines.append(f"{env_var}={port}  # {description}")
        lines.append("")

    # Add preserved non-port variables
    if non_port_vars:
        lines.append("# Other Configuration")
        for key, value in sorted(non_port_vars.items()):
            lines.append(f"{key}={value}")
        lines.append("")

    env_content = '\n'.join(lines)
    env_path.write_text(env_content)
    print(f"✓ Updated {env_path}")

    if non_port_vars:
        print(f"  Preserved {len(non_port_vars)} existing environment variables")

    return env_path


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate random available ports and update .env file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_ports.py              # Generate ports, preserve other .env vars
  python generate_ports.py --fresh      # Generate ports, overwrite entire .env
  python generate_ports.py --dry-run    # Show what would be generated
        """
    )
    parser.add_argument(
        '--fresh',
        action='store_true',
        help='Overwrite .env completely (don\'t preserve non-port variables)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be generated without modifying .env'
    )

    args = parser.parse_args()

    project_name = get_project_name()
    print(f"🔧 {project_name} - Port Configuration Generator")
    print("=" * 60)
    print("Generating random available ports...\n")

    try:
        ports = generate_ports()

        print("Generated ports:")
        # Organize output by category
        categories = {}
        for env_var, (_, _, _, description) in PORT_CONFIG.items():
            category = description.split()[0]
            if category not in categories:
                categories[category] = []
            categories[category].append((description, ports[env_var]))

        for category, items in categories.items():
            print(f"\n  {category}:")
            for description, port in items:
                print(f"    {description:.<45} {port}")

        if args.dry_run:
            print("\n⚠️  Dry run mode - .env file not modified")
            return 0

        env_path = update_env_file(ports, preserve_vars=not args.fresh)

        print(f"\n✓ Port configuration saved to {env_path}")
        print("\n📋 Next steps:")
        print("  1. Restart Docker containers: docker compose down && docker compose up -d")
        print("  2. Restart backend server with new ports")
        print("  3. Restart frontend with new ports")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
