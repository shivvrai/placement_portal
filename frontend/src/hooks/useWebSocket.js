import { useEffect, useState, useRef } from 'react';
import { BASE_URL } from '../api/client';

export function useWebSocket(onMessage) {
  const [connected, setConnected] = useState(false);
  const ws = useRef(null);
  const retryCount = useRef(0);
  const maxRetries = 6;
  const timeoutId = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token') || localStorage.getItem('token');
    if (!token) return;

    let userId = null;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      userId = payload.sub;
    } catch (e) {
      return;
    }

    const connect = () => {
      let baseWs = BASE_URL.replace('http:', 'ws:').replace('https:', 'wss:').replace('/api/v1', '');
      ws.current = new WebSocket(`${baseWs}/ws/${userId}?token=${token}`);

      ws.current.onopen = () => {
        setConnected(true);
        retryCount.current = 0;
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type !== 'ping' && onMessage) {
            onMessage(data);
          }
        } catch (err) {
          console.error("WS Parse error", err);
        }
      };

      ws.current.onclose = () => {
        setConnected(false);
        if (retryCount.current < maxRetries) {
          const delay = Math.min(500 * Math.pow(2, retryCount.current), 30000);
          retryCount.current += 1;
          timeoutId.current = setTimeout(connect, delay);
        }
      };
      
      ws.current.onerror = () => {
         ws.current.close();
      }
    };

    connect();

    return () => {
      clearTimeout(timeoutId.current);
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []); // onMessage should ideally be stable

  return { connected };
}
