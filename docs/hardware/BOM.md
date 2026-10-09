# QUANTUM KAVACHA — HARDWARE BILL OF MATERIALS (BOM)

| Item # | Component | Model / Spec | Purpose | Interface | Required / Optional | Est. Cost Range (INR) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Microcontroller Unit | **ESP32-S3-DevKitC-1-N8R8** (Xtensa LX7 Dual-Core, 240MHz, 8MB Flash, 8MB PSRAM) | Cryptographic root-of-trust, eFuse ID, HMAC engine, telemetry publisher | USB-C, Wi-Fi 802.11 b/g/n | **REQUIRED** | ₹550 – ₹750 |
| **2** | Inertial Measurement Unit (IMU) | **MPU6050 / MPU6500 / ICM-20948** (3-axis Accelerometer + 3-axis Gyroscope) | Physical motion fingerprinting, tremor detection, micro-motion baseline | I2C (Address `0x68`) | **REQUIRED** | ₹120 – ₹250 |
| **3** | Magnetometer | **QMC5883L / LIS3MDL** (3-axis Digital Compass) | Ambient geomagnetic field orientation & physical device displacement | I2C (Address `0x0D`) | **RECOMMENDED** | ₹150 – ₹280 |
| **4** | Environmental Sensor | **BME280** (Temperature, Humidity, Barometric Pressure) | Environmental ambient anomaly detection | I2C (Address `0x76`) | Optional | ₹200 – ₹350 |
| **5** | Ambient Light Sensor | **BH1750** (1–65535 lx digital lux meter) | Optical environment verification | I2C (Address `0x23`) | Optional | ₹80 – ₹150 |
| **6** | Current / Power Monitor | **INA219 / INA226** (Bi-directional current & voltage monitor) | Side-channel power consumption profiling | I2C (Address `0x40`) | Optional | ₹140 – ₹220 |
| **7** | Hardware Secure Element | **Microchip ATECC608A / ATECC608B** (CryptoAuthentication) | External hardware secure storage & ECC P-256 private key isolation | I2C (Address `0xC0`) | Optional | ₹300 – ₹500 |
| **8** | Prototyping Breadboard | 400-Point Half-Size Solderless Breadboard | Circuit interconnection | N/A | **REQUIRED** | ₹70 – ₹120 |
| **9** | Jumper Wires | Male-to-Male & Male-to-Female Dupont Wires (Pack of 20) | I2C bus and power routing | N/A | **REQUIRED** | ₹50 – ₹90 |
| **10** | USB Data Cable | USB-A to USB-C (High-Speed Data Cable) | Programming, flashing, and serial telemetry | USB | **REQUIRED** | ₹100 – ₹180 |

### Prototype Total Estimated Cost
- **Core Required Setup (ESP32-S3 + MPU6050 + Wires + Cable):** `₹890 – ₹1,390 INR` (~`$11 – $17 USD`)
- **Full Sensor-Fusion Setup (with Magnetometer & BME280):** `₹1,240 – ₹2,020 INR` (~`$15 – $24 USD`)
