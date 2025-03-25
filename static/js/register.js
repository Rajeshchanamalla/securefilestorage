document.addEventListener("DOMContentLoaded", function () {
    const registerForm = document.getElementById("register-form");
    const otpSection = document.getElementById("otp-section");
    const errorAlert = document.getElementById("error-alert");
    const successAlert = document.getElementById("success-alert");
    const otpForm = document.getElementById("verify-otp-form"); // Select OTP verification form

    function showMessage(alertElement, message, isSuccess = true) {
        if (alertElement) {
            alertElement.style.display = "block";
            alertElement.textContent = message;
            alertElement.classList.toggle("alert-success", isSuccess);
            alertElement.classList.toggle("alert-danger", !isSuccess);
        }
    }

    if (registerForm) {
        registerForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const username = document.querySelector("input[name='username']").value.trim();
            const email = document.querySelector("input[name='email']").value.trim();
            const password = document.querySelector("input[name='password']").value;
            const confirmPassword = document.querySelector("input[name='confirm_password']").value;

            if (!username || !email || !password || !confirmPassword) {
                showMessage(errorAlert, "All fields are required!", false);
                return;
            }

            if (password !== confirmPassword) {
                showMessage(errorAlert, "Passwords do not match!", false);
                return;
            }

            fetch("/register/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: new URLSearchParams({
                    username: username,
                    email: email,
                    password: password,
                    confirm_password: confirmPassword,
                    action: "register"
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    showMessage(successAlert, "OTP sent to your email!");
                    registerForm.style.display = "none";
                    otpSection.style.display = "block";
                } else {
                    showMessage(errorAlert, data.message, false);
                }
            })
            .catch(error => showMessage(errorAlert, "An error occurred. Please try again.", false));
        });
    }

    // Handle OTP Verification Form Submission
    if (otpForm) {
        otpForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const emailOtp = document.getElementById("email_otp").value.trim();

            if (!emailOtp) {
                showMessage(errorAlert, "OTP is required!", false);
                return;
            }

            fetch("/verify-otp/", {  // Corrected URL for verification
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
                },
                body: new URLSearchParams({
                    email_otp: emailOtp
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    showMessage(successAlert, "Account created! Redirecting to Sign In...");
                    setTimeout(() => {
                        window.location.href = "/signin/";
                    }, 2000);
                } else {
                    showMessage(errorAlert, data.message, false);
                }
            })
            .catch(error => showMessage(errorAlert, "An error occurred. Please try again.", false));
        });
    }
});
