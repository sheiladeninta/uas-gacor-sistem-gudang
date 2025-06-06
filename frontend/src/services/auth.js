const API_URL = 'http://localhost:5001';

export const register = async (userId, nama, password) => {
  try {
    console.log('Sending registration request:', {
      user_id: userId,
      nama: nama,
    });

    const response = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: parseInt(userId),
        nama: nama,
        password: password,
      }),
    });

    const data = await response.json();
    console.log('Registration response:', data);

    if (!response.ok) {
      throw new Error(data.error || 'Registrasi gagal');
    }

    return data;
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

export const login = async (userId, password) => {
  try {
    console.log('Sending login request:', {
      user_id: userId,
    });

    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: parseInt(userId),
        password: password,
      }),
    });

    const data = await response.json();
    console.log('Login response:', data);

    if (!response.ok) {
      throw new Error(data.error || 'Login gagal');
    }

    // Simpan token dan data user di localStorage
    localStorage.setItem('token', data.token);
    localStorage.setItem('user', JSON.stringify(data.user));

    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
};

export const getCurrentUser = () => {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};