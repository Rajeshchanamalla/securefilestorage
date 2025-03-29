import os
import subprocess
import sys
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from .aes_crypto import aes_encrypt, aes_decrypt
from .rsa_crypto import generate_rsa_keys, rsa_encrypt_file, rsa_decrypt_file
from .blowfish_crypto import blowfish_encrypt, blowfish_decrypt
from .hybrid_crypto import hybrid_encrypt, hybrid_decrypt
from .models import DeletedFile, EncryptionHistory


# Get the project base directory dynamically
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS_DIR = os.path.join(BASE_DIR, "keys")  # Ensure keys are stored in the project folder
PUBLIC_KEY_PATH = os.path.join(KEYS_DIR, "public_key.pem")
PRIVATE_KEY_PATH = os.path.join(KEYS_DIR, "private_key.pem")
ATTEMPT_LIMIT = 3  # Maximum allowed password attempts

# Ensure the `keys` directory exists
os.makedirs(KEYS_DIR, exist_ok=True)


# Dictionary to track failed attempts
failed_attempts = {}

def ensure_rsa_keys():
    if not os.path.exists(PRIVATE_KEY_PATH) or not os.path.exists(PUBLIC_KEY_PATH):
        generate_rsa_keys(KEYS_DIR)

def encrypt_file(request):
    try:
        if request.method == "POST" and request.FILES['file']:
            uploaded_file = request.FILES['file']
            fs = FileSystemStorage()
            file_path = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.path(file_path)

            algorithm = request.POST.get("algorithm")
            password = request.POST.get("password", None)
            hybrid_choice = request.POST.get("hybrid_choice", None)

            if algorithm == "AES":
                aes_encrypt(file_path, password)
            elif algorithm == "RSA":
                ensure_rsa_keys()
                rsa_encrypt_file(file_path, PUBLIC_KEY_PATH)
            elif algorithm == "Blowfish":
                blowfish_encrypt(file_path, password)
            elif algorithm == "Hybrid":
                ensure_rsa_keys()
                hybrid_encrypt(file_path, hybrid_choice, password)

            EncryptionHistory.objects.create(
                user=request.user,
                filename=os.path.basename(file_path),
                file_location=file_path,
                encryption_method=algorithm if algorithm != "Hybrid" else f"Hybrid ({hybrid_choice})",
                action_type='ENCRYPT'
            )

            messages.success(request, f"File encrypted successfully: {file_path}.enc")

        return render(request, "encrypt.html")
    except Exception as e:
        messages.error(request, f"An error occurred during encryption: {e}")
        return redirect("encrypt")

def decrypt_file(request):
    try:
        if request.method == "POST" and request.FILES['file']:
            uploaded_file = request.FILES['file']
            fs = FileSystemStorage()
            file_path = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.path(file_path)

            algorithm = request.POST.get("algorithm")
            password = request.POST.get("password", None)
            hybrid_choice = request.POST.get("hybrid_choice", None)

            if algorithm in ["RSA", "Hybrid"]:
                ensure_rsa_keys()

            success = False
            if algorithm == "AES":
                success = aes_decrypt(file_path, password)
            elif algorithm == "RSA":
                success = rsa_decrypt_file(file_path, PRIVATE_KEY_PATH)
            elif algorithm == "Blowfish":
                success = blowfish_decrypt(file_path, password)
            elif algorithm == "Hybrid":
                success = hybrid_decrypt(file_path, hybrid_choice, password)

            if success:
                EncryptionHistory.objects.create(
                    user=request.user,
                    filename=os.path.basename(file_path),
                    file_location=file_path,
                    encryption_method=algorithm if algorithm != "Hybrid" else f"Hybrid ({hybrid_choice})",
                    action_type='DECRYPT'
                )
                messages.success(request, f"File decrypted successfully: {file_path}")
            else:
                messages.error(request, "Decryption failed. Incorrect password or invalid file.")

        return render(request, "decrypt.html")
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")
        return redirect("decrypt")

@login_required
def history(request):
    encrypt_history = EncryptionHistory.objects.filter(user=request.user, action_type='ENCRYPT').order_by('-timestamp')
    decrypt_history = EncryptionHistory.objects.filter(user=request.user, action_type='DECRYPT').order_by('-timestamp')
    return render(request, "history.html", {
        "encrypt_history": encrypt_history,
        "decrypt_history": decrypt_history
    })