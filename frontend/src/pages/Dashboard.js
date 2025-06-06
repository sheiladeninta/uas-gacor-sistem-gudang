import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
} from '@mui/material';
import { getCurrentUser, logout } from '../services/auth';
import {
  Inventory as InventoryIcon,
  LocalShipping as ShippingIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';

function StatCard({ title, value, icon, color }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box
            sx={{
              backgroundColor: `${color}20`,
              borderRadius: '50%',
              p: 1,
              mr: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {React.cloneElement(icon, { sx: { color: color } })}
          </Box>
          <Typography variant="h6" component="div">
            {title}
          </Typography>
        </Box>
        <Typography variant="h4" component="div">
          {value}
        </Typography>
      </CardContent>
    </Card>
  );
}

function WelcomeCard() {
  const user = getCurrentUser();
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" component="div" sx={{ mb: 1 }}>
          Selamat datang, {user?.nama}!
        </Typography>
        <Typography variant="body2" color="text.secondary">
          User ID: {user?.user_id}
        </Typography>
      </CardContent>
    </Card>
  );
}

function Dashboard() {
  const navigate = useNavigate();
  const user = getCurrentUser();

  useEffect(() => {
    if (!user) {
      navigate('/');
    }
  }, [user, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  if (!user) {
    return null;
  }

  // Ini adalah data dummy, nanti bisa diganti dengan data dari API
  const stats = [
    {
      title: 'Total Barang',
      value: '1,234',
      icon: <InventoryIcon />,
      color: '#2196f3',
    },
    {
      title: 'Pengiriman Aktif',
      value: '45',
      icon: <ShippingIcon />,
      color: '#4caf50',
    },
    {
      title: 'Stok Menipis',
      value: '12',
      icon: <WarningIcon />,
      color: '#ff9800',
    },
    {
      title: 'Pertumbuhan',
      value: '+15%',
      icon: <TrendingUpIcon />,
      color: '#9c27b0',
    },
  ];

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 4 }}>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <WelcomeCard />
        </Grid>

        {stats.map((stat) => (
          <Grid item xs={12} sm={6} md={3} key={stat.title}>
            <StatCard {...stat} />
          </Grid>
        ))}

        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: '400px' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Grafik Pengiriman
            </Typography>
            {/* Di sini bisa ditambahkan komponen grafik */}
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '400px' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Aktivitas Terbaru
            </Typography>
            {/* Di sini bisa ditambahkan daftar aktivitas */}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard; 