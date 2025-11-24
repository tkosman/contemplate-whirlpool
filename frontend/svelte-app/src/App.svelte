<script>
  import { onMount, onDestroy } from 'svelte';
  
  let message = 'Connecting...';
  let connected = false;
  let ws = null;
  
  function connectWebSocket() {
    // Use the current protocol and host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = window.location.port;
    
    // If running on dev server (port 5173), connect directly to backend
    // If running on Docker (port 1111), use the proxied WebSocket
    let wsUrl;
    if (port === '5173') {
      // Dev mode: connect directly to backend on port 1234
      wsUrl = `${protocol}//${host}:1234/ws`;
    } else {
      // Production/Docker: connect through nginx proxy on same port
      wsUrl = `${protocol}//${host}:${port}/ws`;
    }
    
    console.log('Connecting to:', wsUrl);
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      connected = true;
      message = 'Connected! Waiting for messages...';
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      message = event.data;
      console.log('Received:', event.data);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      message = 'Connection error!';
      connected = false;
    };
    
    ws.onclose = () => {
      connected = false;
      message = 'Disconnected. Reconnecting...';
      console.log('WebSocket disconnected');
      
      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        connectWebSocket();
      }, 3000);
    };
  }
  
  onMount(() => {
    connectWebSocket();
  });
   
  onDestroy(() => {
    if (ws) {
      ws.close();
    }
  });
</script>

<main>
  <h1>Contemplate Whirlpool</h1>
  <div class="status">
    <span class="indicator" class:connected={connected}></span>
    {connected ? 'Connected' : 'Disconnected'}
  </div>
  <div class="message-box">
    {message}
  </div>
</main>

<style>
  main {
    text-align: center;
    padding: 2rem;
    max-width: 600px;
    margin: 0 auto;
  }
  
  h1 {
    color: #ff3e00;
    font-size: 2.5em;
    margin-bottom: 1em;
  }
  
  .status {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5em;
    margin-bottom: 2em;
    font-size: 1.1em;
    font-weight: 500;
  }
  
  .indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: #ef4444;
    transition: background-color 0.3s;
  }
  
  .indicator.connected {
    background-color: #22c55e;
  }
  
  .message-box {
    border: 3px solid #ff3e00;
    border-radius: 12px;
    padding: 2em;
    min-height: 150px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5em;
    font-weight: 600;
    background: linear-gradient(135deg, #ffffff 0%, #fff5f5 100%);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    word-wrap: break-word;
  }
  
  @media (prefers-color-scheme: dark) {
    .message-box {
      background: linear-gradient(135deg, #1a1a1a 0%, #2a1a1a 100%);
      color: #fff;
    }
  }
</style>
