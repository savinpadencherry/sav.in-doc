async function handleLogin(username, password) {
    try {
        const response = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        if (response.success) {
            localStorage.setItem('authToken', response.user.id);
            showNotification('Logged in successfully', 'success');
            window.location.href = '/upload';
        } else {
            showNotification(response.message || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showNotification('Login failed', 'error');
    }
}

async function handleRegister(username, email, password) {
    try {
        const response = await apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
        if (response.success) {
            showNotification('Account created successfully', 'success');
            window.location.href = '/';
        } else {
            showNotification(response.message || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showNotification('Registration failed', 'error');
    }
}

