import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Typography,
  Box,
  CircularProgress
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { api } from '../services/api';

function PositionsTable() {
  const queryClient = useQueryClient();

  const { data: positions, isLoading } = useQuery('positions', api.getPositions, {
    refetchInterval: 1000
  });

  const closeMutation = useMutation(
    (positionId) => api.closePosition({ position_id: Number(positionId) }),
    {
      onSuccess: () => queryClient.invalidateQueries('positions')
    }
  );

  if (isLoading) {
    return <CircularProgress />;
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Open Positions
      </Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Symbol</TableCell>
              <TableCell align="right">Quantity</TableCell>
              <TableCell align="right">Average Cost</TableCell>
              <TableCell align="right">Market Price</TableCell>
              <TableCell align="right">P&L</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {positions?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No open positions
                </TableCell>
              </TableRow>
            ) : (
              positions?.map((position) => (
                <TableRow key={position.contract.conId}>
                  <TableCell>{position.contract.localSymbol}</TableCell>
                  <TableCell align="right">{position.position}</TableCell>
                  <TableCell align="right">${position.avgCost.toFixed(2)}</TableCell>
                  <TableCell align="right">${position.marketPrice.toFixed(2)}</TableCell>
                  <TableCell 
                    align="right"
                    sx={{ 
                      color: position.unrealizedPNL >= 0 ? 'success.main' : 'error.main',
                      fontWeight: 'bold'
                    }}
                  >
                    ${position.unrealizedPNL.toFixed(2)}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="contained"
                      color="error"
                      size="small"
                      onClick={() => closeMutation.mutate(position.contract.conId)}
                    >
                      Close
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

export default PositionsTable; 