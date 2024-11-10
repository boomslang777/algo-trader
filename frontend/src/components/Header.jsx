import { AppBar, Toolbar, Typography, Box, Skeleton } from '@mui/material';
import { useQueryClient } from 'react-query';
import { useState, useEffect } from 'react';

function Header() {
  const queryClient = useQueryClient();
  const [pnl, setPnl] = useState({
    totalPnL: 0,
    unrealizedPnL: 0,
    realizedPnL: 0
  });

  // Subscribe to PnL updates from WebSocket data
  useEffect(() => {
    const unsubscribe = queryClient.getQueryCache().subscribe(() => {
      const data = queryClient.getQueryData('pnl');
      if (data) {
        setPnl(data);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [queryClient]);

  return (
    <AppBar position="static" elevation={0}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Trading Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            Total P&L:
            <span style={{ 
              color: pnl.totalPnL >= 0 ? '#4caf50' : '#f44336',
              marginLeft: '8px'
            }}>
              ${pnl.totalPnL.toFixed(2)}
            </span>
          </Typography>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Header; 