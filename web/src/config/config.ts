const backend_url =
  process.env.NEXT_PUBLIC_BACKEND_URL || 'https://telegram-group-sentiment-analysis.onrender.com';
const ws_url =
  process.env.NEXT_PUBLIC_WS_URL || 'wss://telegram-group-sentiment-analysis.onrender.com';

console.log(`Backend URL: ${backend_url}`);
console.log(`WS URL: ${ws_url}`);

export { backend_url, ws_url };
