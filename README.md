# WebSocket Chat Server

A FastAPI-based WebSocket server that supports real-time chat with multi-user messaging, graceful shutdown capabilities, and Redis-based broadcasting for multi-worker support.

## Features

- **WebSocket Chat**: Real-time bidirectional communication at `/ws`
- **Multi-User Chat**: Messages from one user appear in all connected clients
- **Connection Management**: Tracks and manages active WebSocket connections
- **Periodic Notifications**: Sends test notifications every 10 seconds to all connected clients
- **Manual Notifications**: API endpoint to send notifications on demand
- **Graceful Shutdown**: Waits for all connections to close (up to 30 minutes) before shutting down
- **Multi-Worker Support**: Each worker process independently manages its connections during shutdown
- **Redis Backend**: Uses Redis for broadcasting messages across multiple workers
- **Modern Chat UI**: Telegram-like chat interface with message bubbles

## Installation

### Docker Setup (Recommended)

1. **(only once) Create .env file with environment variables from the template. Edit the created `.env` file with your parameters:**
   ```bash
   cp .env.example .env
   # edit .env file as you need
   ```

2. **Build the Docker image:**
   ```bash
   make build
   ```

3. **Start services:**
   ```bash
   make up
   ```

4. **Verify services are running:**
   ```bash
   make ps
   ```

The server will be available at `http://localhost:8000`

### Local Development (Optional)

If you want to run locally without Docker:

```bash
# Create virtual environment
python3 -m venv env
source env/bin/activate

# Edit .env file as you need
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn websocket.main:app --host 0.0.0.0 --port 8000 --reload
```

## Usage

### Web Interface

1. Open your browser and navigate to `http://localhost:8000`
2. Click "Connect" to establish a WebSocket connection
3. Type messages and send them - they will appear in all connected windows
4. Open multiple browser windows/tabs to see multi-user chat in action

### API Endpoints

#### WebSocket: `/ws`

Connect to this endpoint to receive real-time notifications and send messages.

**Client Example (JavaScript)**:
```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Received:", data);
};
ws.send(JSON.stringify({type: "notification", message: "Hello!"}));
```

#### GET `/`

Returns an HTML chat interface for testing WebSocket connections in a browser.

#### POST `/notify`

Send a notification to all connected clients.

**Example**:
```bash
curl -X POST "http://localhost:8000/notify?message=Hello%20World"
```

**Response**:
```json
{
    "status": "success",
    "message": "Notification sent to 5 clients"
}
```

## Message Types

The server sends different types of messages:

- **`welcome`**: Sent when a client first connects
- **`notification`**: Periodic or manual notifications
- **`echo`**: Broadcast messages from other users (for chat functionality)
- **`shutdown_notice`**: Sent when server is shutting down

## Architecture

### Project Structure

```
.
├── websocket/              # Main application code
│   ├── main.py            # FastAPI app and lifespan
│   ├── interfaces/        # API endpoints
│   │   └── api/
│   │       ├── ws.py      # WebSocket endpoint
│   │       └── http.py    # HTTP endpoints
│   ├── services/          # Business logic
│   │   ├── manager.py     # Connection management
│   │   ├── unit_of_work.py # Unit of Work pattern
│   │   ├── notifier.py    # Periodic notifications
│   │   └── shutdown.py    # Graceful shutdown
│   ├── core/              # Configuration and middleware
│   │   ├── settings.py    # Application settings
│   │   ├── logging.py     # Logging configuration
│   │   └── middleware.py  # Request middleware
│   ├── domain/            # Domain entities
│   │   └── entities.py    # Message types
│   └── templates/         # HTML templates
│       └── main.html      # Chat interface
├── docker-compose.yml     # Docker configuration
├── Dockerfile             # Docker image definition
├── Makefile              # Build and run commands
```

### Key Components

- **ConnectionTracker**: Manages WebSocket connections and uses Redis for broadcasting
- **BroadcastUnitOfWork**: Implements Unit of Work pattern for WebSocket connections
- **Redis Broadcasting**: Messages are broadcast via Redis to support multi-worker deployments

## Docker Commands

Using the Makefile:

```bash
make build      # Build Docker images
make up         # Start services
make down       # Stop services
make restart    # Restart services
make logs       # View service logs
make ps         # Show running services
make test       # Run tests
make clean      # Remove containers and volumes
```

Or using Docker Compose directly:

```bash
docker compose up -d        # Start services
docker compose down         # Stop services
docker compose logs -f      # View logs
docker compose ps           # Show status
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
REDIS_HOST=redis
REDIS_PORT=6379
API_PORT=8000
LOG_LEVEL=INFO
SHUTDOWN_TIMEOUT=1800
PERIODIC_NOTIFICATION=10
```

### Settings

The application uses environment variables with defaults defined in `websocket/core/settings.py`:

- `REDIS_HOST`: Redis hostname (default: `redis`)
- `REDIS_PORT`: Redis port (default: `6379`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `SHUTDOWN_TIMEOUT`: Graceful shutdown timeout in seconds (default: `1800` = 30 minutes)
- `PERIODIC_NOTIFICATION`: Interval for periodic notifications in seconds (default: `10`)

## Graceful Shutdown

When the server receives a SIGTERM or SIGINT signal:

1. **Shutdown Initiation**: 
   - New connections are rejected
   - All active clients receive a shutdown notice
   - Background tasks are cancelled

2. **Connection Waiting**:
   - Server waits for all active connections to close naturally
   - Progress is logged every 5 seconds showing:
     - Number of active connections
     - Remaining time until timeout

3. **Timeout Handling**:
   - If 30 minutes pass and connections still exist, they are force-closed
   - Server then shuts down

4. **Multi-Worker Behavior**:
   - Each worker process handles shutdown independently
   - Logs include process ID (PID) for tracking
   - Each worker waits for its own connections to close

## Testing

### Run Tests

```bash
# Run all tests
make test

# Or use the test script directly
pytest

```

## Troubleshooting

### Services won't start

```bash
# Check Docker logs
make logs

# Check if ports are in use
lsof -i :8000
lsof -i :6379

# Restart services
make restart
```

### Connection issues

- Verify Redis is running: `docker compose ps redis`
- Check WebSocket endpoint: `curl http://localhost:8000/status`
- View application logs: `make logs`

### Messages not appearing in other windows

- Ensure Redis is running and accessible
- Check that all windows are connected (status shows "Connected")
- Verify broadcaster is connected (check logs for connection errors)
