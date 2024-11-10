import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Alert,
  Divider
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useState, useEffect } from 'react';
import { api } from '../services/api';

function Settings() {
  const queryClient = useQueryClient();
  const [localSettings, setLocalSettings] = useState(null);
  const [spyPrice, setSpyPrice] = useState(null);
  const [availableStrikes, setAvailableStrikes] = useState({ calls: [], puts: [] });
  const [saveStatus, setSaveStatus] = useState(null);

  const { data: settings } = useQuery('settings', api.getSettings, {
    onSuccess: (data) => {
      if (!localSettings) {
        setLocalSettings(data);
      }
    }
  });

  useQuery('spy-price', api.getSpyPrice, {
    refetchInterval: 5000,
    onSuccess: (data) => {
      setSpyPrice(data.price);
      const baseStrike = Math.round(data.price);
      
      // Generate strikes for calls (ATM + 2 OTM)
      const calls = [baseStrike];
      for (let i = 1; i <= 2; i++) {
        calls.push(baseStrike + i);
      }
      
      // Generate strikes for puts (ATM + 2 OTM)
      const puts = [baseStrike];
      for (let i = 1; i <= 2; i++) {
        puts.push(baseStrike - i);
      }
      
      setAvailableStrikes({ calls, puts });
    }
  });

  const updateSettingsMutation = useMutation(
    (newSettings) => api.updateSettings(newSettings),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('settings');
        setSaveStatus('success');
        setTimeout(() => setSaveStatus(null), 3000);
      },
      onError: () => {
        setSaveStatus('error');
        setTimeout(() => setSaveStatus(null), 3000);
      }
    }
  );

  const handleSettingChange = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    const newSettings = { ...localSettings, [field]: value };
    setLocalSettings(newSettings);
    updateSettingsMutation.mutate(newSettings);
  };

  if (!localSettings) return null;

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h5" gutterBottom>
        Trading Settings
      </Typography>
      
      {saveStatus && (
        <Alert 
          severity={saveStatus === 'success' ? 'success' : 'error'}
          sx={{ mb: 2 }}
        >
          {saveStatus === 'success' ? 'Settings saved successfully' : 'Error saving settings'}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Position Size
              </Typography>
              <TextField
                fullWidth
                type="number"
                label="Quantity"
                value={localSettings.quantity}
                onChange={handleSettingChange('quantity')}
                InputProps={{ inputProps: { min: 1 } }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                SPY Options Settings
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography color="primary" variant="h6">
                  Current SPY Price: ${spyPrice?.toFixed(2) || 'Loading...'}
                </Typography>
              </Box>

              <Grid container spacing={2}>
                {/* Calls */}
                <Grid item xs={6}>
                  <FormControl fullWidth>
                    <InputLabel>Call Strike</InputLabel>
                    <Select
                      value={localSettings.call_strike || ''}
                      onChange={handleSettingChange('call_strike')}
                      label="Call Strike"
                    >
                      {availableStrikes.calls.map((strike) => (
                        <MenuItem key={`call-${strike}`} value={strike}>
                          ${strike} {strike === Math.round(spyPrice || 0) ? '(ATM)' : '(OTM)'}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                {/* Puts */}
                <Grid item xs={6}>
                  <FormControl fullWidth>
                    <InputLabel>Put Strike</InputLabel>
                    <Select
                      value={localSettings.put_strike || ''}
                      onChange={handleSettingChange('put_strike')}
                      label="Put Strike"
                    >
                      {availableStrikes.puts.map((strike) => (
                        <MenuItem key={`put-${strike}`} value={strike}>
                          ${strike} {strike === Math.round(spyPrice || 0) ? '(ATM)' : '(OTM)'}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>

              <Box sx={{ mt: 2 }}>
                <FormControl fullWidth>
                  <InputLabel>Expiration</InputLabel>
                  <Select
                    value={localSettings.dte}
                    onChange={handleSettingChange('dte')}
                    label="Expiration"
                  >
                    <MenuItem value={0}>0 DTE (Today)</MenuItem>
                    <MenuItem value={1}>1 DTE (Tomorrow)</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Settings;