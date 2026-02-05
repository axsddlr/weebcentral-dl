import { useEffect, useRef, useCallback, useState } from 'react';

interface UseWebSocketOptions {
  /** WebSocket path, e.g. '/ws/progress' */
  path: string;
  /** Called for each incoming JSON message */
  onMessage?: (data: any) => void;
  /** Auto-reconnect delay in ms (default: 3000) */
  reconnectDelay?: number;
}

export function useWebSocket({ path, onMessage, reconnectDelay = 3000 }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}${path}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessageRef.current?.(data);
      } catch {
        // ignore non-JSON messages
      }
    };

    ws.onclose = () => {
      setConnected(false);
      setTimeout(() => connect(), reconnectDelay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [path, reconnectDelay]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected };
}
