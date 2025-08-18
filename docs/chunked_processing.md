# Chunked Message Processing

## Overview

The `get_group_messages` function has been enhanced to support chunked processing of large volumes of messages. This feature allows the system to efficiently handle groups with thousands of messages by processing them in smaller, manageable chunks.

## How It Works

### Chunked Processing Algorithm

1. **Configurable Chunk Size**: Messages are processed in chunks of 100 by default (configurable)
2. **Pagination**: Uses Telegram's `offset_id` parameter to paginate through messages
3. **Date Range Filtering**: Only processes messages within the specified date range
4. **Incremental Saving**: Each chunk is saved to the database as it's processed
5. **Memory Efficiency**: Prevents memory issues when dealing with large message volumes

### Key Features

- **Backward Compatible**: Existing code continues to work without changes
- **Configurable**: Chunk size can be adjusted based on system requirements
- **Resilient**: Handles network issues and API limits gracefully
- **Progress Tracking**: Detailed logging shows progress through chunks

## Usage

### Basic Usage (Default Chunk Size)

```python
# Uses default chunk size of 100
messages = await analyzer.get_group_messages(group_info, days=30)
```

### Custom Chunk Size

```python
# Process messages in chunks of 50
messages = await analyzer.get_group_messages(group_info, days=30, chunk_size=50)

# Process messages in chunks of 200
messages = await analyzer.get_group_messages(group_info, days=30, chunk_size=200)
```

## Benefits

1. **Memory Management**: Prevents out-of-memory errors with large groups
2. **Progress Visibility**: Users can see progress as chunks are processed
3. **Fault Tolerance**: If one chunk fails, others can still be processed
4. **Database Efficiency**: Messages are saved incrementally rather than all at once
5. **API Rate Limiting**: Reduces the risk of hitting Telegram API limits

## Logging

The system provides detailed logging for monitoring chunked processing:

```
INFO: Fetching messages from the last 60 days in chunks of 100...
INFO: Fetching chunk 1 (offset_id: 0)
INFO: Processing chunk 1 with 100 messages
INFO: Chunk 1: Saved 95 new messages, skipped 5 existing messages
INFO: Total messages processed so far: 100
INFO: Fetching chunk 2 (offset_id: 12345)
INFO: Processing chunk 2 with 100 messages
INFO: Chunk 2: Saved 98 new messages, skipped 2 existing messages
INFO: Total messages processed so far: 200
INFO: Reached messages older than 60 days, stopping fetch
INFO: Retrieved 200 total messages from 200 total messages processed
```

## Performance Considerations

- **Chunk Size**: Smaller chunks (50-100) are better for memory usage
- **Network**: Larger chunks may be more efficient for network usage
- **Database**: Each chunk triggers a database save operation
- **API Limits**: Telegram has rate limits that may affect chunk processing speed

## Error Handling

The chunked processing includes robust error handling:

- **Network Errors**: Individual chunk failures don't stop the entire process
- **API Limits**: Automatic retry mechanisms for rate limiting
- **Date Range**: Stops processing when messages are older than the specified range
- **Fallback**: Uses cached messages if fresh fetching fails

## Configuration

The chunk size can be configured based on your system's capabilities:

- **Low Memory Systems**: Use chunk_size=50
- **High Memory Systems**: Use chunk_size=200
- **Network Constrained**: Use chunk_size=100 (default)
- **High Performance**: Use chunk_size=500 (use with caution) 