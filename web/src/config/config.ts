const backend_url =
  process.env.NEXT_PUBLIC_BACKEND_URL || 'https://telegram-group-sentiment-analysis.onrender.com';
const ws_url =
  process.env.NEXT_PUBLIC_WS_URL || 'wss://telegram-group-sentiment-analysis.onrender.com';
const fetchStatusInterval = parseInt(process.env.NEXT_PUBLIC_FETCH_INTERVAL ?? '5000', 10);

export { backend_url, ws_url, fetchStatusInterval };
