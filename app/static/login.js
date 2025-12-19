// Login page JavaScript

const loginForm = document.getElementById("login-form")
const signupForm = document.getElementById("signup-form")
const toggleBtn = document.getElementById("toggle-btn")
const toggleText = document.getElementById("toggle-text")
const authTitle = document.getElementById("auth-title")
const authSubtitle = document.getElementById("auth-subtitle")
const errorMessage = document.getElementById("error-message")

let isLoginMode = true

// Toggle between login and signup
toggleBtn.addEventListener("click", () => {
    isLoginMode = !isLoginMode

    if (isLoginMode) {
        // Switch to login
        loginForm.classList.remove("hidden")
        signupForm.classList.add("hidden")
        authTitle.textContent = "Welcome Back"
        authSubtitle.textContent = "Sign in to continue your strategic analysis"
        toggleText.textContent = "Don't have an account?"
        toggleBtn.textContent = "Sign Up"
    } else {
        // Switch to signup
        loginForm.classList.add("hidden")
        signupForm.classList.remove("hidden")
        authTitle.textContent = "Create Account"
        authSubtitle.textContent = "Join Stratagem AI to unlock strategic insights"
        toggleText.textContent = "Already have an account?"
        toggleBtn.textContent = "Sign In"
    }

    // Clear error
    hideError()
    lucide.createIcons()
})

// Handle login
loginForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    hideError()

    const email = document.getElementById("login-email").value
    const password = document.getElementById("login-password").value
    const btn = document.getElementById("login-btn")

    try {
        btn.disabled = true
        btn.innerHTML = '<div class="spinner"></div>'

        const response = await fetch("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        })

        const data = await response.json()

        if (!response.ok) {
            throw new Error(data.detail || "Login failed")
        }

        // Store token
        localStorage.setItem("auth_token", data.access_token)
        localStorage.setItem("user_email", data.user.email)

        // Redirect to dashboard
        window.location.href = "/"
    } catch (error) {
        showError(error.message)
        btn.disabled = false
        btn.innerHTML = '<span>Sign In</span><i data-lucide="arrow-right"></i>'
        lucide.createIcons()
    }
})

// Handle signup
signupForm.addEventListener("submit", async (e) => {
    e.preventDefault()
    hideError()

    const email = document.getElementById("signup-email").value
    const password = document.getElementById("signup-password").value
    const passwordConfirm = document.getElementById("signup-password-confirm").value
    const btn = document.getElementById("signup-btn")

    // Validate passwords match
    if (password !== passwordConfirm) {
        showError("Passwords do not match")
        return
    }

    // Validate password length
    if (password.length < 6) {
        showError("Password must be at least 6 characters")
        return
    }

    try {
        btn.disabled = true
        btn.innerHTML = '<div class="spinner"></div>'

        const response = await fetch("/auth/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        })

        const data = await response.json()

        if (!response.ok) {
            throw new Error(data.detail || "Signup failed")
        }

        // Store token
        localStorage.setItem("auth_token", data.access_token)
        localStorage.setItem("user_email", data.user.email)

        // Redirect to dashboard
        window.location.href = "/"
    } catch (error) {
        showError(error.message)
        btn.disabled = false
        btn.innerHTML = '<span>Create Account</span><i data-lucide="arrow-right"></i>'
        lucide.createIcons()
    }
})

// Show error message
function showError(message) {
    errorMessage.textContent = message
    errorMessage.classList.remove("hidden")
}

// Hide error message
function hideError() {
    errorMessage.classList.add("hidden")
}

// Check if already logged in
const token = localStorage.getItem("auth_token")
if (token) {
    // Verify token is valid
    fetch("/auth/me", {
        headers: { Authorization: `Bearer ${token}` },
    })
        .then((response) => {
            if (response.ok) {
                // Already logged in, redirect to dashboard
                window.location.href = "/"
            }
        })
        .catch(() => {
            // Token invalid, clear it
            localStorage.removeItem("auth_token")
            localStorage.removeItem("user_email")
        })
}
