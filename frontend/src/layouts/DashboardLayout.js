import React, { useState } from 'react';
import { Box, CssBaseline, useTheme } from '@mui/material';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';

const drawerWidth = 240; // Pastikan lebar sidebar konsisten

function DashboardLayout({ children }) {
  const theme = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false); // State untuk mengontrol sidebar

  const handleDrawerToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column' }}>
      <CssBaseline />
      <Navbar handleDrawerToggle={handleDrawerToggle} />
      <Box sx={{ display: 'flex', flexGrow: 1 }}>
        <Sidebar open={sidebarOpen} onClose={handleSidebarClose} />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3, // Padding menggunakan sistem spacing
            marginTop: '64px',
            boxSizing: 'border-box',
            transition: theme.transitions.create(['margin', 'width'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.leavingScreen,
            }),
            marginLeft: 0, // Default margin 0 ketika sidebar temporary
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
}

export default DashboardLayout; 