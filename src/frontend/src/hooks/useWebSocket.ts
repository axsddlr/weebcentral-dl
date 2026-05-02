import { useEffect, useRef, useCallback, useState } from 'react';

interface WsMessage {
  type: string;
  data: unknown;
}

interface UseWebSocketOptions {
  path: string;
  onMessage?: (data: WsMessage) => void;
  reconnectDelay?: number;
}

export function useWebSocket({ path, onMessage, reconnectDelay = 3000 }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [connected, setConnected] = useState(false);
  const onMessageRef = useRef(onMessage);
  const connectRef = useRef<(() => void) | undefined>(undefined);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}${path}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsMessage;
        onMessageRef.current?.(data);
      } catch {
        // ignore non-JSON messages
      }
    };

    ws.onclose = () => {
      setConnected(false);
      reconnectTimerRef.current = setTimeout(() => connectRef.current?.(), reconnectDelay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [path, reconnectDelay]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected };
}
