# ESP32-S3 HARDWARE SECURITY HARDENING GUIDE
**Target Hardware**: Espressif ESP32-S3 (WROOM-1 / DevKitC-1)  
**Security Level**: Hardware-Rooted Trust Node for Financial Attestation  
**Platform**: QUANTUM KAVACHA

---

## 1. DEVELOPMENT MODE VS HARDENED PRODUCTION MODE

> [!CAUTION]
> **CRITICAL WARNING**: ESP32-S3 eFuses are one-time programmable (OTP) physical silicon fuses. Once blown, eFuse states **CANNOT BE REVERSED**. Blowing incorrect eFuses will permanently brick the development board.

| Security Feature | Development / Hackathon Demo Mode | Hardened Production Mode |
| :--- | :--- | :--- |
| **eFuse MAC Identity** | Read factory-burned MAC (`esp_efuse_mac_get_default`) | Read factory-burned MAC with read-protect disabled |
| **HMAC Secret Key** | Pre-shared key in protected firmware memory | Burned into `BLOCK4_KEY0` (write/read protected) |
| **Secure Boot v2** | Software digest verification (`SIMULATED`) | Hardware RSA-3072 / ECDSA signature verification |
| **Flash Encryption** | Plaintext SPI flash communication | AES-XTS-256 hardware flash encryption enabled |
| **JTAG / UART Debug** | Enabled for serial telemetry & debugging | Permanently disabled via `DIS_PAD_JTAG` eFuse |
| **Firmware Update** | PlatformIO USB flashing | Encrypted & Signed OTA update only |

---

## 2. PRODUCTION eFUSE PROVISIONING PROCEDURE

### Step 1: Generate Cryptographic Keys
On a secure, air-gapped provisioning workstation:
```bash
# 1. Generate Secure Boot v2 RSA-3072 Private Signing Key
espsecure.py generate_signing_key --version 2 secure_boot_signing_key.pem

# 2. Extract Public Key Digest
espsecure.py digest_rsa_public_key --keyfile secure_boot_signing_key.pem --output public_key_digest.bin

# 3. Generate 256-bit Flash Encryption Key
espsecure.py generate_flash_encryption_key flash_encryption_key.bin

# 4. Generate 256-bit HMAC Key for Attestation
python -c "import secrets; open('hmac_attestation_key.bin','wb').write(secrets.token_bytes(32))"
```

---

### Step 2: Burn Keys into ESP32-S3 eFuses
```bash
# 1. Burn Secure Boot Digest into BLOCK0/BLOCK1
espefuse.py --port COM_PORT burn_key BLOCK_KEY0 public_key_digest.bin SECURE_BOOT_DIGEST0

# 2. Burn Flash Encryption Key into BLOCK_KEY1
espefuse.py --port COM_PORT burn_key BLOCK_KEY1 flash_encryption_key.bin FLASH_ENCRYPT_256

# 3. Burn HMAC Key into BLOCK_KEY2 (Purpose: HMAC_UPSTREAM)
espefuse.py --port COM_PORT burn_key BLOCK_KEY2 hmac_attestation_key.bin HMAC_UPSTREAM

# 4. Enable Secure Boot v2 & Flash Encryption
espefuse.py --port COM_PORT burn_efuse SECURE_BOOT_EN
espefuse.py --port COM_PORT burn_efuse FLASH_CRYPT_CNT 0x7F
```

---

### Step 3: Disable Debug Interfaces (Final Production Lock)
```bash
# Permanently disable JTAG debugging, ROM download mode, and direct memory access
espefuse.py --port COM_PORT burn_efuse DIS_PAD_JTAG
espefuse.py --port COM_PORT burn_efuse DIS_DOWNLOAD_MODE
espefuse.py --port COM_PORT burn_efuse DIS_DIRECT_BOOT
```

---

## 3. HARDWARE ATT-STATION PROTOCOL IMPLEMENTATION
In firmware (`firmware/esp32_s3_trust_node/src/main.cpp`):
1. The ESP32-S3 listens for challenge nonces from Quantum Kavacha over USB CDC / WiFi TLS.
2. It fetches the hardware HMAC key directly from `BLOCK_KEY2` using the ESP-IDF HMAC peripheral API:
   ```c
   esp_hmac_calculate(HMAC_KEY2, (uint8_t*)message, message_len, hmac_output);
   ```
3. The monotonic anti-rollback counter stored in non-volatile flash / RTC memory is incremented and included in the signed payload.
4. Telemetry is dispatched to the backend for verification against `_consumed_nonces` and registered baselines.

---

## 4. PHYSICAL ANTI-TAMPER GUIDELINES
For deployed physical Point-of-Sale / Banking Trust Nodes:
1. **Conformal Coating**: Encapsulate the ESP32-S3 module and sensor array in opaque epoxy to prevent micro-probing of I2C traces.
2. **Mesh Ground Plane**: Use a top-layer PCB enclosure mesh connected to a GPIO tamper-detect interrupt; cutting the mesh triggers instantaneous key zeroization in RTC RAM.
3. **Quiescent Sensor Calibration**: Place the device in its permanent orientation during enrollment; any physical displacement $> 15^\circ$ or continuous vibrational anomaly triggers immediate attestation revocation.
