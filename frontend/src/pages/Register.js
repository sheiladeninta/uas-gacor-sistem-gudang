import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Alert,
  Link,
} from '@mui/material';
import { register } from '../services/auth';

function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    userId: '',
    nama: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Validasi khusus untuk User ID
    if (name === 'userId') {
      // Hanya terima angka
      if (value === '' || /^\d+$/.test(value)) {
        setFormData(prev => ({
          ...prev,
          [name]: value
        }));
      }
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validasi User ID
    if (!formData.userId) {
      setError('User ID harus diisi');
      return;
    }

    // Validasi nama
    if (!formData.nama.trim()) {
      setError('Nama harus diisi');
      return;
    }

    // Validasi password
    if (formData.password.length < 6) {
      setError('Password minimal 6 karakter');
      return;
    }

    // Validasi konfirmasi password
    if (formData.password !== formData.confirmPassword) {
      setError('Password dan konfirmasi password tidak sesuai');
      return;
    }

    try {
      console.log('Attempting registration with:', {
        userId: formData.userId,
        nama: formData.nama,
      });
      
      await register(formData.userId, formData.nama, formData.password);
      console.log('Registration successful');
      
      // Redirect ke halaman login setelah registrasi berhasil
      navigate('/');
    } catch (error) {
      console.error('Registration error:', error);
      setError(error.message);
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            padding: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
          <Typography component="h1" variant="h5">
            Registrasi Akun
          </Typography>
          {error && (
            <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
              {error}
            </Alert>
          )}
          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="userId"
              label="User ID"
              name="userId"
              autoComplete="userId"
              autoFocus
              value={formData.userId}
              onChange={handleChange}
              inputProps={{ inputMode: 'numeric', pattern: '[0-9]*' }}
              helperText="User ID harus berupa angka"
            />
            <TextField
              margin="normal"
              required
              fullWidth
              id="nama"
              label="Nama Lengkap"
              name="nama"
              autoComplete="name"
              value={formData.nama}
              onChange={handleChange}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="new-password"
              value={formData.password}
              onChange={handleChange}
              helperText="Password minimal 6 karakter"
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="Konfirmasi Password"
              type="password"
              id="confirmPassword"
              autoComplete="new-password"
              value={formData.confirmPassword}
              onChange={handleChange}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
            >
              Daftar
            </Button>
            <Box sx={{ textAlign: 'center' }}>
              <Link href="/" variant="body2">
                Sudah punya akun? Login
              </Link>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}

export default Register; 