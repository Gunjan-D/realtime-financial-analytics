import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Grid,
  Paper,
  Box,
  Chip,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  ShowChart,
  Assessment,
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import './App.css';

interface StockData {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
}

interface MarketSummary {
  total_symbols: number;
  avg_change_percent: number;
  gainers: StockData[];
  losers: StockData[];
  most_active: StockData[];
  market_sentiment: string;
}

function App() {
  const [stocks, setStocks] = useState<StockData[]>([]);
  const [marketSummary, setMarketSummary] = useState<MarketSummary | null>(null);
  const [selectedStock, setSelectedStock] = useState<string>('AAPL');
  const [historicalData, setHistoricalData] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  // Fetch all stocks data
  const fetchStocks = async () => {
    try {
      const response = await fetch('/api/v1/stocks');
      const data = await response.json();
      setStocks(data.stocks);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('Error fetching stocks:', error);
    }
  };

  // Fetch market summary
  const fetchMarketSummary = async () => {
    try {
      const response = await fetch('/api/v1/market/summary');
      const data = await response.json();
      setMarketSummary(data);
    } catch (error) {
      console.error('Error fetching market summary:', error);
    }
  };

  // Fetch historical data for selected stock
  const fetchHistoricalData = async (symbol: string) => {
    try {
      const response = await fetch(`/api/v1/stocks/${symbol}/history?days=7`);
      const data = await response.json();
      
      // Format data for charts
      const formattedData = data.history.slice(0, 50).reverse().map((item: any) => ({
        time: new Date(item.timestamp).toLocaleTimeString(),
        price: item.price,
        volume: item.volume,
      }));
      
      setHistoricalData(formattedData);
    } catch (error) {
      console.error('Error fetching historical data:', error);
      // Generate mock historical data for demo
      const mockData = Array.from({ length: 50 }, (_, i) => ({
        time: new Date(Date.now() - (49 - i) * 60000).toLocaleTimeString(),
        price: 150 + Math.random() * 20 - 10,
        volume: Math.floor(Math.random() * 1000000),
      }));
      setHistoricalData(mockData);
    }
  };

  // Setup WebSocket connection for real-time updates
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'market_update') {
          setStocks(message.data.stocks);
          setLastUpdate(new Date().toLocaleTimeString());
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
    
    // Cleanup on unmount
    return () => {
      ws.close();
    };
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchStocks();
    fetchMarketSummary();
    fetchHistoricalData(selectedStock);
    
    // Fallback polling if WebSocket fails
    const interval = setInterval(() => {
      if (!isConnected) {
        fetchStocks();
        fetchMarketSummary();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [isConnected]);

  // Update historical data when selected stock changes
  useEffect(() => {
    fetchHistoricalData(selectedStock);
  }, [selectedStock]);

  const formatPrice = (price: number) => `$${price.toFixed(2)}`;
  const formatChange = (change: number, changePercent: number) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)} (${sign}${changePercent.toFixed(2)}%)`;
  };

  const getChangeColor = (change: number) => change >= 0 ? '#4caf50' : '#f44336';

  return (
    <div className="App">
      <AppBar position="static" sx={{ backgroundColor: '#1976d2' }}>
        <Toolbar>
          <ShowChart sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Real-time Financial Analytics Dashboard
          </Typography>
          <Chip 
            icon={isConnected ? <TrendingUp /> : <TrendingDown />}
            label={isConnected ? 'Live' : 'Disconnected'}
            color={isConnected ? 'success' : 'error'}
            variant="outlined"
          />
          <Typography variant="body2" sx={{ ml: 2 }}>
            Last Update: {lastUpdate}
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {/* Market Summary Cards */}
        {marketSummary && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Market Sentiment
                  </Typography>
                  <Typography variant="h5" component="div">
                    <Chip 
                      label={marketSummary.market_sentiment.toUpperCase()}
                      color={marketSummary.market_sentiment === 'bullish' ? 'success' : 'error'}
                    />
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Avg Change
                  </Typography>
                  <Typography 
                    variant="h5" 
                    component="div"
                    sx={{ color: getChangeColor(marketSummary.avg_change_percent) }}
                  >
                    {marketSummary.avg_change_percent > 0 ? '+' : ''}{marketSummary.avg_change_percent.toFixed(2)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Active Symbols
                  </Typography>
                  <Typography variant="h5" component="div">
                    {marketSummary.total_symbols}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Top Gainer
                  </Typography>
                  <Typography variant="h6" component="div">
                    {marketSummary.gainers[0]?.symbol}
                  </Typography>
                  <Typography 
                    variant="body2" 
                    sx={{ color: getChangeColor(marketSummary.gainers[0]?.change_percent || 0) }}
                  >
                    +{marketSummary.gainers[0]?.change_percent.toFixed(2)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        <Grid container spacing={3}>
          {/* Stock Price Chart */}
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" component="div">
                  {selectedStock} - Price Chart (Live)
                </Typography>
                <Box>
                  {['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA'].map((symbol) => (
                    <Chip
                      key={symbol}
                      label={symbol}
                      onClick={() => setSelectedStock(symbol)}
                      color={selectedStock === symbol ? 'primary' : 'default'}
                      sx={{ ml: 1 }}
                    />
                  ))}
                </Box>
              </Box>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#8884d8" 
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Grid>

          {/* Market Lists */}
          <Grid item xs={12} md={4}>
            <Grid container spacing={2}>
              {/* Top Gainers */}
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" component="div" sx={{ mb: 2 }}>
                    <TrendingUp sx={{ mr: 1, color: '#4caf50' }} />
                    Top Gainers
                  </Typography>
                  <List dense>
                    {marketSummary?.gainers.slice(0, 5).map((stock, index) => (
                      <ListItem key={stock.symbol} divider={index < 4}>
                        <ListItemText
                          primary={stock.symbol}
                          secondary={formatPrice(stock.price)}
                        />
                        <Typography 
                          variant="body2" 
                          sx={{ color: getChangeColor(stock.change_percent) }}
                        >
                          +{stock.change_percent.toFixed(2)}%
                        </Typography>
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              </Grid>

              {/* Top Losers */}
              <Grid item xs={12}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" component="div" sx={{ mb: 2 }}>
                    <TrendingDown sx={{ mr: 1, color: '#f44336' }} />
                    Top Losers
                  </Typography>
                  <List dense>
                    {marketSummary?.losers.slice(0, 5).map((stock, index) => (
                      <ListItem key={stock.symbol} divider={index < 4}>
                        <ListItemText
                          primary={stock.symbol}
                          secondary={formatPrice(stock.price)}
                        />
                        <Typography 
                          variant="body2" 
                          sx={{ color: getChangeColor(stock.change_percent) }}
                        >
                          {stock.change_percent.toFixed(2)}%
                        </Typography>
                      </ListItem>
                    ))}
                  </List>
                </Paper>
              </Grid>
            </Grid>
          </Grid>

          {/* All Stocks Table */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" component="div" sx={{ mb: 2 }}>
                <Assessment sx={{ mr: 1 }} />
                All Stocks (Real-time)
              </Typography>
              <Grid container spacing={2}>
                {stocks.slice(0, 15).map((stock) => (
                  <Grid item xs={12} sm={6} md={4} key={stock.symbol}>
                    <Card 
                      variant="outlined" 
                      sx={{ cursor: 'pointer' }}
                      onClick={() => setSelectedStock(stock.symbol)}
                    >
                      <CardContent>
                        <Typography variant="h6" component="div">
                          {stock.symbol}
                        </Typography>
                        <Typography variant="h5" sx={{ mb: 1 }}>
                          {formatPrice(stock.price)}
                        </Typography>
                        <Typography 
                          variant="body2" 
                          sx={{ color: getChangeColor(stock.change_percent) }}
                        >
                          {formatChange(stock.change, stock.change_percent)}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Vol: {stock.volume.toLocaleString()}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </div>
  );
}

export default App;