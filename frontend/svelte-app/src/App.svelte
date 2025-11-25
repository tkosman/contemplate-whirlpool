<script>
  import { onMount, onDestroy, afterUpdate } from 'svelte';

  const APP_VERSION = '1.0.2';

  let messages = [];
  let connected = false;
  let ws = null;
  let messageContainer;

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
      addMessage('Connected! Waiting for messages...', 'system');
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      addMessage(event.data, 'message');
      console.log('Received:', event.data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      addMessage('Connection error!', 'error');
      connected = false;
    };

    ws.onclose = () => {
      connected = false;
      addMessage('Disconnected. Reconnecting...', 'system');
      console.log('WebSocket disconnected');

      // Attempt to reconnect after 3 seconds
      setTimeout(() => {
        connectWebSocket();
      }, 3000);
    };
  }

  function addMessage(text, type = 'message') {
    const timestamp = new Date().toLocaleTimeString();
    messages = [...messages, { text, type, timestamp, id: Date.now() }];
  }

  function clearMessages() {
    messages = [];
  }

  // Auto-scroll to bottom when new messages arrive
  afterUpdate(() => {
    if (messageContainer) {
      messageContainer.scrollTop = messageContainer.scrollHeight;
    }
  });

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
  <div class="header">
    <div class="status">
      <span class="indicator" class:connected={connected}></span>
      {connected ? 'Connected' : 'Disconnected'}
    </div>
    <button on:click={clearMessages}>Clear</button>
  </div>
  <div class="message-box" bind:this={messageContainer}>
    {#if messages.length === 0}
      <div class="empty">Waiting for messages...</div>
    {:else}
      {#each messages as msg (msg.id)}
        <div class="message {msg.type}">
          <span class="timestamp">{msg.timestamp}</span>
          <span class="text">{msg.text}</span>
        </div>
      {/each}
    {/if}
  </div>
  <div class="version">v{APP_VERSION}</div>
</main>

<style>
  main {
    padding: 2rem;
    max-width: 800px;
    margin: 0 auto;
  }

  h1 {
    color: #ff3e00;
    font-size: 2.5em;
    margin-bottom: 0.5em;
    text-align: center;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1em;
  }

  .status {
    display: flex;
    align-items: center;
    gap: 0.5em;
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

  button {
    padding: 0.5em 1em;
    background-color: #ff3e00;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: background-color 0.2s;
  }

  button:hover {
    background-color: #e63900;
  }

  .message-box {
    border: 3px solid #ff3e00;
    border-radius: 12px;
    padding: 1em;
    height: 500px;
    overflow-y: auto;
    background: linear-gradient(135deg, #ffffff 0%, #fff5f5 100%);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .empty {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #999;
    font-size: 1.2em;
  }

  .message {
    padding: 0.75em;
    margin-bottom: 0.5em;
    border-radius: 6px;
    display: flex;
    gap: 1em;
    align-items: baseline;
    animation: slideIn 0.2s ease-out;
  }

  .message.message {
    background-color: rgba(100, 108, 255, 0.1);
  }

  .message.system {
    background-color: rgba(34, 197, 94, 0.1);
    font-style: italic;
  }

  .message.error {
    background-color: rgba(239, 68, 68, 0.1);
    color: #dc2626;
  }

  .timestamp {
    font-size: 0.85em;
    color: #666;
    font-family: monospace;
    white-space: nowrap;
  }

  .text {
    flex: 1;
    word-wrap: break-word;
    font-size: 1em;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @media (prefers-color-scheme: dark) {
    .message-box {
      background: linear-gradient(135deg, #1a1a1a 0%, #2a1a1a 100%);
      color: #fff;
    }

    .message.message {
      background-color: rgba(100, 108, 255, 0.2);
    }

    .message.system {
      background-color: rgba(34, 197, 94, 0.2);
    }

    .message.error {
      background-color: rgba(239, 68, 68, 0.2);
      color: #fca5a5;
    }

    .timestamp {
      color: #999;
    }
  }
</style>
