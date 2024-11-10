import { useEffect, useRef, useCallback } from 'react';
import { Grid, Paper, Box } from '@mui/material';
import TradingToggle from './TradingToggle';
import PositionsTable from './PositionsTable';
import OrdersTable from './OrdersTable';
import Settings from './Settings';
import { useQueryClient } from 'react-query';

function Dashboard() {
  const wsRef = useRef(null);
  const queryClient = useQueryClient();

  const handleWebSocketMessage = useCallback((event) => {
    try {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'data':
          if (data.data.positions || data.data.orders || data.data.pnl) {
            queryClient.setQueryData('positions', data.data.positions);
            queryClient.setQueryData('orders', data.data.orders);
            queryClient.setQueryData('pnl', data.data.pnl);
          }
          break;
      }
    } catch (err) {
      console.error('Error processing message:', err);
    }
  }, [queryClient]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return;

    const ws = new WebSocket('ws://localhost:8000/ws');
    wsRef.current = ws;
    ws.onmessage = handleWebSocketMessage;

    ws.onclose = () => {
      wsRef.current = null;
      // Simple reconnect after 1 second
      setTimeout(connect, 1000);
    };
  }, [handleWebSocketMessage]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <TradingToggle />
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, minHeight: '400px' }}>
            <PositionsTable />
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, minHeight: '400px' }}>
            <OrdersTable />
          </Paper>
        </Grid>
        
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Settings />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;