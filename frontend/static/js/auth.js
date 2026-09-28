/**
 * EcoGreen Authentication Client Module
 */

function getCurrentUser() {
    const userJson = localStorage.getItem('current_user');
    return userJson ? JSON.parse(userJson) : null;
}

function setCurrentUser(user) {
    if (user) {
        localStorage.setItem('current_user', JSON.stringify(user));
    } else {
        localStorage.removeItem('current_user');
    }
}

function logoutUser() {
    API.setToken(null);
    setCurrentUser(null);
    window.location.href = '/';
}

async function handleLoginSubmit(username, password) {
    try {
        const response = await API.post('/login', { username, password });
        if (response.access_token) {
            API.setToken(response.access_token);
            setCurrentUser({
                id: response.user_id,
                username: response.username,
                user_type: response.user_type
            });
            return response;
        }
        throw new Error("Invalid response from server");
    } catch (err) {
        console.error("Login failed:", err);
        throw err;
    }
}

async function handleRegisterSubmit(userData) {
    try {
        return await API.post('/users', userData);
    } catch (err) {
        console.error("Registration failed:", err);
        throw err;
    }
}

window.getCurrentUser = getCurrentUser;
window.setCurrentUser = setCurrentUser;
window.logoutUser = logoutUser;
window.handleLoginSubmit = handleLoginSubmit;
window.handleRegisterSubmit = handleRegisterSubmit;
