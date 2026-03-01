# In The Beginning -- PHP Snapshot Server

A cosmic evolution simulator written in PHP, served as an auto-refreshing
HTML snapshot via PHP's built-in web server. Simulates the universe from the
Big Bang through the emergence of life.

## Prerequisites

- PHP 8.0 or later (CLI with built-in web server)
- No Composer dependencies

## Project Structure

```
php/
  server.php               # HTTP server router and entry point
  simulate.php             # CLI simulation runner
  simulator/
    Constants.php          # Physical constants and epoch definitions
    Quantum.php            # Quantum field simulation
    Atomic.php             # Atomic nucleosynthesis
    Chemistry.php          # Chemical bonding and molecules
    Biology.php            # Biological emergence
    Environment.php        # Environmental conditions
    Universe.php           # Top-level simulation orchestrator
  templates/
    snapshot.php           # HTML template for the web snapshot
  public/
    style.css              # Stylesheet for the web UI
```

## Run (Web Server)

Start the built-in PHP development server:

```sh
php -S 0.0.0.0:8080 server.php
```

Open http://localhost:8080 in a browser. The page auto-refreshes every
10 seconds to show updated simulation state.

## API Endpoints

| Endpoint      | Method | Description                          |
|---------------|--------|--------------------------------------|
| `/`           | GET    | HTML snapshot of simulation state    |
| `/api/state`  | GET    | JSON snapshot of current state       |
| `/api/reset`  | GET    | Reset simulation with a new seed     |
| `/style.css`  | GET    | Stylesheet                           |

## Run (CLI)

```sh
php simulate.php
```

## Notes

- No external dependencies; uses only PHP standard library functions.
- The server uses `declare(strict_types=1)`.
- Simulation state persists across requests within a single server process.
- CORS headers are set on `/api/state` for cross-origin access.
