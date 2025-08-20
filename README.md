## AI POWERED SECOND BRAIN

A production-ready Personalized AI Powered second brain assistant.

## 🚀 Production Features

- **MongoDB Storage**: Session data, messages, and analysis results stored in MongoDB
- **Caching**: Intelligent message caching to reduce API calls
- **Docker Support**: Complete containerized deployment
- **Scalable**: Designed for production workloads
- **Session Management**: Secure session storage in database
- **Real-Time Messaging**: WebSocket-like functionality for live message reception


## 🛠️ Production Setup

### 1. Environment Configuration

Copy the example environment file:
```bash
cp env.example .env
```

Edit `.env` with your credentials:

Start the production stack:
```bash
docker-compose up -d
```

This will start:
- MongoDB database
- Personal Assistant application

### 3. Local Development

Install dependencies:
```bash
uv sync
```

Run the production version:
```bash
uv run uvicorn src.main:app --reload 2>&1 | tee out.log
```

## 📈 MongoDB Collections

The application creates the following collections:

- **sessions**: Telegram session data
- **groups**: Group information and metadata
- **messages**: Cached message data
- **analyses**: Analysis results and reports

## 🔧 Production Configuration


### Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f persona_ai 

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## 📊 Usage

### Batch Analysis Mode
1. **First Run**: The application will prompt for Telegram verification code
2. **Group Selection**: Choose from available groups
3. **Analysis**: View comprehensive analysis including:
   - Total messages and unique users
   - Sentiment distribution
   - Top active users
   - Average sentiment scores


**Features:**
- Real-time message reception
- Automatic sentiment analysis
- Custom message handlers per group
- MongoDB storage of real-time messages
- Event-driven architecture similar to WebSockets

## Formatting and tooling 

If precommit hook not installed 

```bash
pre-commit install
```
Before pushing any changes run the following code. However if you don't run run it it will run during commit messages.

```bash
uv run pre-commit run --all-files
```

## 🔒 Security

- Session data stored securely in MongoDB
- No local file storage
- Environment-based configuration
- Containerized deployment

## 📝 Logs

Application logs are stored in out.log when running locally.

## 🚀 Scaling

For high-volume production:

1. **MongoDB Replica Set**: Configure MongoDB replica set for high availability
2. **Load Balancer**: Use nginx or similar for multiple instances
3. **Redis Caching**: Add Redis for additional caching layer
4. **Monitoring**: Add Prometheus/Grafana for metrics

## 🔧 Troubleshooting

### No Messages Found
- Check group permissions
- Verify group has text messages
- Increase time period in code

### MongoDB Connection Issues
- Verify MongoDB is running: `docker-compose ps`
- Check connection string in `.env`
- View logs: `docker-compose logs mongodb`

### Session Issues
- Clear MongoDB sessions collection
- Re-authenticate with Telegram
