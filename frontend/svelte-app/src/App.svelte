<script>
  import { onMount, onDestroy, afterUpdate } from 'svelte';

  const APP_VERSION = '1.0.12';

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
      try {
        const data = JSON.parse(event.data);
        addMessage(data.thought, 'message', data.thinker || 'Unknown');
      } catch (e) {
        // Fallback for non-JSON messages
        addMessage(event.data, 'message', null);
      }
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

  function addMessage(text, type = 'message', thinker = null) {
    const timestamp = new Date().toLocaleTimeString();
    messages = [...messages, { text, type, timestamp, thinker, id: Date.now() }];
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
    <a href="https://www.buymeacoffee.com/tymoteusz4development" target="_blank" class="bmc-link">
      <img src="https://cdn.buymeacoffee.com/buttons/v2/default-red.png" alt="Buy Me A Coffee" class="bmc-button" />
    </a>
  </div>
  <div class="message-box" bind:this={messageContainer}>
    {#if messages.length === 0}
      <div class="empty">Waiting for messages...</div>
    {:else}
      {#each messages as msg (msg.id)}
        <div class="message {msg.type}">
          <span class="timestamp">{msg.timestamp}</span>
          {#if msg.thinker}
            <span class="thinker">{msg.thinker}</span>
          {/if}
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
    gap: 1em;
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
    align-items: center;
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
    min-width: 80px;
  }

  .thinker {
    font-size: 0.85em;
    color: #ff3e00;
    font-weight: 600;
    white-space: nowrap;
    padding: 0.2em 0.6em;
    background-color: rgba(255, 62, 0, 0.1);
    border-radius: 4px;
    min-width: 150px;
    text-align: center;
  }

  .text {
    flex: 1;
    word-wrap: break-word;
    font-size: 1em;
  }

  .version {
    margin-top: 1.5em;
    text-align: center;
    color: white;
    font-size: 0.9em;
  }

  .bmc-link {
    display: flex;
    align-items: center;
  }

  .bmc-button {
    height: 40px;
    width: auto;
    transition: transform 0.2s ease;
  }

  .bmc-button:hover {
    transform: scale(1.05);
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

  /* Mobile responsive styles */
  @media (max-width: 768px) {
    main {
      padding: 0.5rem;
      max-width: 100%;
    }

    h1 {
      font-size: 1.6em;
      margin-bottom: 0.3em;
    }

    .header {
      flex-direction: column;
      gap: 0.5em;
      margin-bottom: 0.75em;
    }

    .status {
      font-size: 0.95em;
    }

    .bmc-button {
      height: 32px;
    }

    .message-box {
      height: calc(100vh - 200px);
      min-height: 250px;
      padding: 0.5em;
      border-width: 2px;
    }

    .version {
      margin-top: 0.75em;
      font-size: 0.8em;
    }

    .message {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.5em;
      padding: 0.75em;
    }

    .timestamp {
      min-width: auto;
      font-size: 0.75em;
    }

    .thinker {
      min-width: auto;
      font-size: 0.75em;
      padding: 0.25em 0.5em;
    }

    .text {
      font-size: 0.95em;
      width: 100%;
    }
  }

  @media (max-width: 480px) {
    main {
      padding: 0.25rem;
    }

    h1 {
      font-size: 1.4em;
      margin-bottom: 0.25em;
    }

    .message-box {
      height: calc(100vh - 180px);
      padding: 0.4em;
      border-width: 2px;
    }

    .header {
      gap: 0.4em;
      margin-bottom: 0.5em;
    }

    .status {
      font-size: 0.9em;
    }

    .bmc-button {
      height: 28px;
    }

    .version {
      margin-top: 0.5em;
      font-size: 0.75em;
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

    .thinker {
      color: #ff8866;
      background-color: rgba(255, 136, 102, 0.2);
    }
  }
</style>
