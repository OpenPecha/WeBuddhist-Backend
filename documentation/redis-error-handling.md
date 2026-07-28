# Redis Error Handling

The application provides clear, actionable error messages when Redis is not available or not configured correctly.

## Error Messages

### 1. Redis Connection Refused (Server Not Running)

**When:** Redis/Dragonfly is not running on the configured host:port

**Error Message:**
```
❌ REDIS CONNECTION FAILED: Cannot connect to Redis at redis://localhost:6379/0
   - Make sure Redis/Dragonfly is running
   - Check REDIS_URL config: redis://localhost:6379/0
   - Try: docker run -d -p 6379:6379 redis:latest
   Error: [Errno 111] Connection refused
```

**Solution:**
```bash
# Start Redis in Docker
docker run -d -p 6379:6379 redis:latest

# Or if using Dragonfly
docker run -d -p 6379:6379 eresdb/dragonfly:latest

# Or install locally (macOS with Homebrew)
brew install redis
brew services start redis
```

### 2. Redis Timeout (Connection Hangs)

**When:** Redis is not responding or network is unreachable

**Error Message:**
```
❌ REDIS TIMEOUT: Connection to Redis at redis://localhost:6379/0 timed out
   - Redis may be unresponsive or overloaded
   - Check REDIS_URL: redis://localhost:6379/0
   Error: Timeout connecting to Redis
```

**Solution:**
- Check if Redis is running: `redis-cli ping`
- Check network connectivity: `ping localhost`
- Verify REDIS_URL in environment variables
- Restart Redis and the application

### 3. Invalid Redis URL

**When:** REDIS_URL configuration is malformed

**Error Message:**
```
❌ REDIS INITIALIZATION FAILED: InvalidURL
   - Redis URL: redis://invalid:url:format
   - Error: Invalid URL format
   - Make sure Redis/Dragonfly is running and accessible
```

**Solution:**
Valid REDIS_URL formats:
- Local: `redis://localhost:6379/0`
- Remote: `redis://user:password@host:port/db`
- Dragonfly: `redis://localhost:6379/0`

### 4. Broadcaster Not Initialized (Runtime)

**When:** App started but broadcaster failed to initialize

**Error Message on app startup:**
```
❌ Comment broadcaster not initialized.
   - Make sure Redis/Dragonfly is running
   - Check REDIS_URL configuration
   - App startup failed - check server logs for Redis connection errors
```

**Solution:**
- See error message during app startup
- Fix REDIS_URL or start Redis
- Restart application

### 5. Redis Connection Lost (During Operation)

**When:** Redis crashes or network disconnects after app startup

**Error Message in WebSocket:**
```
❌ Redis connection lost.
   - Redis/Dragonfly may have crashed
   - Network connection may be down
   - Restart Redis and restart the application
```

**Client receives:**
- WebSocket closes with code 1011 (Server Error)
- Reason: "Redis unavailable"
- Browser page shows "🔴 Disconnected"

**Solution:**
1. Check if Redis is still running: `redis-cli ping`
2. Restart Redis if needed
3. Restart the FastAPI application
4. Users will auto-reconnect when app is back online

## Configuration

### Environment Variable

Set REDIS_URL before starting the app:

```bash
# Local Redis
export REDIS_URL="redis://localhost:6379/0"

# Remote Redis with auth
export REDIS_URL="redis://user:password@redis.example.com:6379/0"

# Dragonfly (drop-in Redis replacement)
export REDIS_URL="redis://localhost:6379/0"
```

### Default Value

If not set, defaults to: `redis://localhost:6379/0`

### Check Configuration

```bash
# View current REDIS_URL
echo $REDIS_URL

# Or from within Python
from pecha_api.config import get
print(get("REDIS_URL"))
```

## Testing Redis Connection

### From Command Line

```bash
# Test if Redis is running
redis-cli ping
# Response: PONG

# Check if the app can connect
redis-cli -h localhost -p 6379 ping

# Connect to specific DB
redis-cli -n 0 ping
```

### From Python

```python
import asyncio
from redis.asyncio import Redis

async def test_redis():
    try:
        redis = await Redis.from_url("redis://localhost:6379/0")
        pong = await redis.ping()
        print(f"✅ Redis is working: {pong}")
        await redis.close()
    except Exception as e:
        print(f"❌ Redis error: {e}")

asyncio.run(test_redis())
```

## Logs to Check

All Redis errors are logged with:
- ❌ prefix for clarity
- Full error details
- Configuration that was attempted
- Suggested fixes

**Log locations:**
- Docker: `docker logs <container_name>`
- File: Check configured log file path
- Stdout: If running in terminal

**Sample log entry:**
```
ERROR    pecha_api.db.mongo_database:mongo_database.py:58 ❌ REDIS CONNECTION FAILED: Cannot connect to Redis at redis://localhost:6379/0
   - Make sure Redis/Dragonfly is running
   - Check REDIS_URL config: redis://localhost:6379/0
   - Try: docker run -d -p 6379:6379 redis:latest
   Error: [Errno 111] Connection refused
```

## WebSocket Behavior with Redis Errors

### App Won't Start
- Application startup fails
- Server returns 500 for all requests
- WebSocket endpoint returns 500
- Browser shows connection error

### Redis Crashes After Start
- App continues running
- WebSocket connections close with code 1011
- Browser page shows "🔴 Disconnected"
- Auto-reconnect attempts every 3 seconds
- Will reconnect when Redis is back online

### Slow Redis Response
- Comments take longer to broadcast
- WebSocket stays connected
- No error shown to user (just slower)

## Recovery Steps

If Redis fails:

1. **Identify the issue** — Check logs for error message above
2. **Fix configuration** — Verify REDIS_URL is correct
3. **Restart Redis** — Stop and start Redis service
4. **Verify connectivity** — Test with `redis-cli ping`
5. **Restart app** — Application will reconnect automatically
6. **Users auto-reconnect** — WebSocket pages will refresh on reconnect

## Monitoring

To monitor Redis health:

```bash
# Watch Redis info
watch redis-cli info stats

# Check memory usage
redis-cli info memory

# List all keys
redis-cli --scan

# Monitor in real-time
redis-cli monitor
```
