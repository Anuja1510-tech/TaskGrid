// Authentication functionality for landing page
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 TaskGrid Landing Page Loaded');
    
    // Check if user is already logged in
    if (window.api && window.api.isAuthenticated()) {
        console.log('User already authenticated, redirecting...');
        // Redirect to dashboard if already logged in
        window.location.href = '../dashboard/dashboard-enhanced.html';
    }

    // Helper function for element selection
    const $ = (selector) => document.querySelector(selector);

    // Login functionality
    const loginBtn = $("#loginBtn");
    if (loginBtn) {
        loginBtn.addEventListener("click", async () => {
            console.log('Login button clicked');
            
            const username = $("#loginUsername").value.trim();
            const password = $("#loginPassword").value;

            if (!username || !password) {
                Utils.showToast("Please enter both username and password", 'error');
                return;
            }

            try {
                Utils.setLoading(loginBtn, true);
                console.log('Attempting login...');
                
                const response = await api.login(username, password);
                console.log('Login response:', response);
                
                Utils.showToast("Login successful! Redirecting...", 'success');
                
                // Redirect to dashboard after successful login
                setTimeout(() => {
                    window.location.href = '../dashboard/dashboard-enhanced.html';
                }, 1500);
                
            } catch (error) {
                console.error('Login error:', error);
                Utils.handleApiError(error, 'during login');
            } finally {
                Utils.setLoading(loginBtn, false);
            }
        });
    } else {
        console.error('Login button not found');
    }

    // Signup redirect
    const signupBtn = $("#signupBtn");
    if (signupBtn) {
        signupBtn.addEventListener("click", () => {
            console.log('Signup button clicked');
            window.location.href = '../signup/signup-fixed.html';
        });
    }

    // Enter key support for login
    const usernameInput = $("#loginUsername");
    const passwordInput = $("#loginPassword");
    
    if (usernameInput) {
        usernameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && loginBtn) {
                loginBtn.click();
            }
        });
    }
    
    if (passwordInput) {
        passwordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && loginBtn) {
                loginBtn.click();
            }
        });
    }

    // Test backend connection on page load
    setTimeout(async () => {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/health`);
            if (response.ok) {
                console.log('✅ Backend connection successful');
                Utils.showToast('Connected to TaskGrid backend', 'success');
            } else {
                console.warn('⚠️ Backend responded with error');
                Utils.showToast('Backend connection issue', 'warning');
            }
        } catch (error) {
            console.error('❌ Backend connection failed:', error);
            Utils.showToast('Cannot connect to backend. Make sure server is running on port 5000.', 'error');
        }
    }, 1000);

    console.log('🎯 Authentication handlers initialized');
});