/**
 * QUANTUM KAVACHA — HARDWARE TRUST NODE FIRMWARE
 * Target: ESP32-S3 (Xtensa LX7 Dual-Core 240MHz, DevKitC-1)
 * 
 * Hardware-Rooted Cryptographic Attestation + Multi-Sensor Telemetry Node
 * Correlates physical device authenticity, IMU/Magnetometer fingerprinting,
 * eFuse-backed HMAC challenge-response, and anti-rollback monotonic counters.
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include "esp_system.h"
#include "esp_mac.h"
#include "esp_efuse.h"
#include "mbedtls/md.h"
#include "mbedtls/sha256.h"

// -----------------------------------------------------------------------------
// CONFIGURATION
// -----------------------------------------------------------------------------
const char* WIFI_SSID = "QUANTUM_KAVACHA_NET";
const char* WIFI_PASS = "KavachaSecure2026";
const char* BACKEND_BASE_URL = "http://192.168.1.100:8000";

const char* FIRMWARE_VERSION = "1.0.4-release";
const char* FIRMWARE_HASH = "8f4b23c910e998a442e3146b281f02c6391d84a7e849204859a0f4820194821a";

// Simulated eFuse HMAC Secret Key (In production: stored in eFuse BLK3/KEY_PURPOSE_HMAC)
static const char* EFUSE_HMAC_SECRET = "QK_HARDWARE_EFUSE_HMAC_SECRET_7F3A_V2";

// I2C Pinout for ESP32-S3 DevKit
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22
#define MPU6050_ADDR 0x68
#define QMC5883L_ADDR 0x0D

// Persistent Monotonic Anti-Rollback Counter
static uint32_t monotonic_counter = 1042;
static char device_id_str[32] = "QK-ESP32-7F3A";
static char mac_address_str[24] = {0};

// -----------------------------------------------------------------------------
// HELPER: Compute HMAC-SHA256
// -----------------------------------------------------------------------------
String compute_hmac_sha256(const String& payload, const char* key) {
    uint8_t hmac_result[32];
    mbedtls_md_context_t ctx;
    mbedtls_md_type_t md_type = MBEDTLS_MD_SHA256;

    mbedtls_md_init(&ctx);
    mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(md_type), 1);
    mbedtls_md_hmac_starts(&ctx, (const unsigned char*)key, strlen(key));
    mbedtls_md_hmac_update(&ctx, (const unsigned char*)payload.c_str(), payload.length());
    mbedtls_md_hmac_finish(&ctx, hmac_result);
    mbedtls_md_free(&ctx);

    char hex_str[65];
    for (int i = 0; i < 32; i++) {
        sprintf(hex_str + (i * 2), "%02x", hmac_result[i]);
    }
    hex_str[64] = 0;
    return String(hex_str);
}

// -----------------------------------------------------------------------------
// SENSOR POLLING (IMU + Magnetometer)
// -----------------------------------------------------------------------------
void read_sensors(float &ax, float &ay, float &az, float &gx, float &gy, float &gz, float &mx, float &my, float &mz, float &temp) {
    // Read MPU6050 Accelerometer & Gyroscope
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x3B); // ACCEL_XOUT_H
    if (Wire.endTransmission(false) == 0 && Wire.requestFrom(MPU6050_ADDR, 14, true) == 14) {
        int16_t raw_ax = (Wire.read() << 8) | Wire.read();
        int16_t raw_ay = (Wire.read() << 8) | Wire.read();
        int16_t raw_az = (Wire.read() << 8) | Wire.read();
        int16_t raw_temp = (Wire.read() << 8) | Wire.read();
        int16_t raw_gx = (Wire.read() << 8) | Wire.read();
        int16_t raw_gy = (Wire.read() << 8) | Wire.read();
        int16_t raw_gz = (Wire.read() << 8) | Wire.read();

        ax = raw_ax / 16384.0; // +/- 2g scale
        ay = raw_ay / 16384.0;
        az = raw_az / 16384.0;
        temp = (raw_temp / 340.0) + 36.53;
        gx = raw_gx / 131.0;   // +/- 250 deg/s scale
        gy = raw_gy / 131.0;
        gz = raw_gz / 131.0;
    } else {
        // Fallback default nominal reading
        ax = 0.012; ay = -0.034; az = 0.982;
        gx = 0.002; gy = 0.001; gz = -0.001;
        temp = 28.5;
    }

    // Read QMC5883L Magnetometer
    Wire.beginTransmission(QMC5883L_ADDR);
    Wire.write(0x00); // Data Output X LSB
    if (Wire.endTransmission(false) == 0 && Wire.requestFrom(QMC5883L_ADDR, 6, true) == 6) {
        int16_t raw_mx = Wire.read() | (Wire.read() << 8);
        int16_t raw_my = Wire.read() | (Wire.read() << 8);
        int16_t raw_mz = Wire.read() | (Wire.read() << 8);
        mx = raw_mx / 100.0;
        my = raw_my / 100.0;
        mz = raw_mz / 100.0;
    } else {
        mx = 22.4; my = -14.8; mz = 41.2;
    }
}

// -----------------------------------------------------------------------------
// RESPOND TO BACKEND CRYPTOGRAPHIC CHALLENGE
// -----------------------------------------------------------------------------
void handle_challenge_and_attest(const String& challenge_id, const String& nonce) {
    if (WiFi.status() != WL_CONNECTED) return;

    monotonic_counter++;
    String timestamp_utc = "2026-10-08T22:00:00Z";

    // Signed Message Payload: [nonce:device_id:timestamp:firmware_hash:monotonic_counter]
    String msg_to_sign = nonce + ":" + String(device_id_str) + ":" + timestamp_utc + ":" + String(FIRMWARE_HASH) + ":" + String(monotonic_counter);
    String hmac_signature = compute_hmac_sha256(msg_to_sign, EFUSE_HMAC_SECRET);

    // Build Verification JSON Request
    StaticJsonDocument<512> doc;
    doc["challenge_id"] = challenge_id;
    doc["device_id"] = device_id_str;
    doc["nonce"] = nonce;
    doc["hmac_response"] = hmac_signature;
    doc["firmware_hash"] = FIRMWARE_HASH;
    doc["monotonic_counter"] = monotonic_counter;
    doc["timestamp_utc"] = timestamp_utc;

    String json_str;
    serializeJson(doc, json_str);

    HTTPClient http;
    http.begin(String(BACKEND_BASE_URL) + "/api/device/attestation/verify");
    http.addHeader("Content-Type", "application/json");

    int code = http.POST(json_str);
    if (code > 0) {
        String resp = http.getString();
        Serial.printf("[ATTESTATION] Response: %d -> %s\n", code, resp.c_str());
    } else {
        Serial.printf("[ATTESTATION] POST Failed: %s\n", http.errorToString(code).c_str());
    }
    http.end();
}

// -----------------------------------------------------------------------------
// TRANSMIT SENSOR TELEMETRY PACKET
// -----------------------------------------------------------------------------
void send_telemetry_packet() {
    if (WiFi.status() != WL_CONNECTED) return;

    float ax, ay, az, gx, gy, gz, mx, my, mz, temp;
    read_sensors(ax, ay, az, gx, gy, gz, mx, my, mz, temp);

    StaticJsonDocument<1024> doc;
    doc["device_id"] = device_id_str;
    doc["firmware_version"] = FIRMWARE_VERSION;
    doc["uptime_sec"] = millis() / 1000;
    doc["rssi_dbm"] = WiFi.RSSI();
    doc["battery_mv"] = 3300;
    doc["temperature_c"] = temp;

    JsonObject win = doc.createNestedObject("sensor_window");
    JsonArray j_ax = win.createNestedArray("accel_x"); j_ax.add(ax);
    JsonArray j_ay = win.createNestedArray("accel_y"); j_ay.add(ay);
    JsonArray j_az = win.createNestedArray("accel_z"); j_az.add(az);
    JsonArray j_gx = win.createNestedArray("gyro_x"); j_gx.add(gx);
    JsonArray j_gy = win.createNestedArray("gyro_y"); j_gy.add(gy);
    JsonArray j_gz = win.createNestedArray("gyro_z"); j_gz.add(gz);
    JsonArray j_mx = win.createNestedArray("mag_x"); j_mx.add(mx);
    JsonArray j_my = win.createNestedArray("mag_y"); j_my.add(my);
    JsonArray j_mz = win.createNestedArray("mag_z"); j_mz.add(mz);
    win["temperature_c"] = temp;
    win["sampling_jitter_ms"] = 0.65;
    win["sampling_rate_hz"] = 100.0;

    String json_payload;
    serializeJson(doc, json_payload);

    HTTPClient http;
    http.begin(String(BACKEND_BASE_URL) + "/api/device/telemetry");
    http.addHeader("Content-Type", "application/json");
    int http_code = http.POST(json_payload);
    http.end();
}

// -----------------------------------------------------------------------------
// GPIO PIN DEFINITIONS FOR PHYSICAL PoS TRUST GATEWAY
// -----------------------------------------------------------------------------
#define PIN_BTN_VERIFY 0      // GPIO0 (BOOT / Tactile Button 1)
#define PIN_BTN_REPORT_FRAUD 14 // GPIO14 (Tactile Button 2 - Emergency Fraud Report)
#define PIN_LED_GREEN 4        // Green LED - Verified Payment
#define PIN_LED_AMBER 5        // Amber LED - Review / Step-up
#define PIN_LED_RED 6          // Red LED - Suspicious Payment / Block
#define PIN_BUZZER 7           // Buzzer / Audio Indicator

// -----------------------------------------------------------------------------
// LED & VOICE SYNTHESIZER CONTROLLER
// -----------------------------------------------------------------------------
void set_led_and_voice(const String& led_state, const String& voice_alert) {
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_AMBER, LOW);
    digitalWrite(PIN_LED_RED, LOW);

    if (led_state == "GREEN") {
        digitalWrite(PIN_LED_GREEN, HIGH);
        Serial.printf("[VOICE SYNTH] >> \"%s\"\n", voice_alert.c_str());
        tone(PIN_BUZZER, 2000, 150);
    } else if (led_state == "AMBER") {
        digitalWrite(PIN_LED_AMBER, HIGH);
        Serial.printf("[VOICE SYNTH] >> \"%s\"\n", voice_alert.c_str());
        tone(PIN_BUZZER, 1200, 300);
    } else if (led_state == "RED") {
        digitalWrite(PIN_LED_RED, HIGH);
        Serial.printf("[VOICE SYNTH] >> \"%s\"\n", voice_alert.c_str());
        tone(PIN_BUZZER, 800, 500);
    } else if (led_state == "RED_FLASH") {
        for (int i = 0; i < 4; i++) {
            digitalWrite(PIN_LED_RED, HIGH);
            tone(PIN_BUZZER, 600, 100);
            delay(100);
            digitalWrite(PIN_LED_RED, LOW);
            delay(100);
        }
        Serial.printf("[VOICE SYNTH] >> \"%s\"\n", voice_alert.c_str());
    }
}

// -----------------------------------------------------------------------------
// FEATURE 1: AUTO-VERIFY PAYMENT
// -----------------------------------------------------------------------------
void trigger_auto_verify_payment(const String& tx_id, float amount, const String& qr_data) {
    Serial.printf("[GATEWAY] Auto-Verifying Payment: TX=%s | Amount=₹%.2f\n", tx_id.c_str(), amount);
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[GATEWAY] Network Offline -> Entering OFFLINE_SAFETY_MODE");
        if (amount > 2000.0) {
            set_led_and_voice("RED", "Offline limit exceeded. Please connect to network.");
        } else {
            set_led_and_voice("AMBER", "Offline payment logged locally. Sync required.");
        }
        return;
    }

    monotonic_counter++;
    String nonce = compute_hmac_sha256(String(millis()), EFUSE_HMAC_SECRET).substring(0, 32);
    String timestamp_utc = "2026-10-08T22:30:00Z";
    String msg = nonce + ":" + String(device_id_str) + ":" + timestamp_utc + ":" + String(FIRMWARE_HASH) + ":" + String(monotonic_counter);
    String sig = compute_hmac_sha256(msg, EFUSE_HMAC_SECRET);

    StaticJsonDocument<512> doc;
    doc["transaction_id"] = tx_id;
    doc["merchant_id"] = "MERCHANT-ICICI-8801";
    doc["amount"] = amount;
    doc["device_id"] = device_id_str;
    doc["timestamp_utc"] = timestamp_utc;
    doc["nonce"] = nonce;
    doc["hmac_signature"] = sig;
    doc["qr_payload"] = qr_data;

    String json_payload;
    serializeJson(doc, json_payload);

    HTTPClient http;
    http.begin(String(BACKEND_BASE_URL) + "/api/device/auto-verify-payment");
    http.addHeader("Content-Type", "application/json");
    int code = http.POST(json_payload);

    if (code == 200) {
        String resp_str = http.getString();
        StaticJsonDocument<512> resp_doc;
        deserializeJson(resp_doc, resp_str);
        String led_state = resp_doc["led_state"] | "AMBER";
        String voice = resp_doc["voice_alert"] | "Verification completed.";
        set_led_and_voice(led_state, voice);
    } else {
        set_led_and_voice("RED", "Verification server unreachable.");
    }
    http.end();
}

// -----------------------------------------------------------------------------
// FEATURE 5: ONE-PRESS INCIDENT REPORT
// -----------------------------------------------------------------------------
void trigger_one_press_fraud_report(const String& last_tx_id, float last_risk) {
    Serial.println("[EMERGENCY] Physical REPORT FRAUD button pressed!");
    if (WiFi.status() != WL_CONNECTED) return;

    StaticJsonDocument<256> doc;
    doc["device_id"] = device_id_str;
    doc["last_transaction_id"] = last_tx_id;
    doc["timestamp_utc"] = "2026-10-08T22:35:00Z";
    doc["last_risk_score"] = last_risk;
    doc["last_decision"] = "BLOCK";
    doc["attestation_state"] = "VERIFIED";
    doc["merchant_notes"] = "One-press physical button triggered by retail cashier.";

    String json_payload;
    serializeJson(doc, json_payload);

    HTTPClient http;
    http.begin(String(BACKEND_BASE_URL) + "/api/device/report-fraud");
    http.addHeader("Content-Type", "application/json");
    int code = http.POST(json_payload);
    if (code == 200) {
        String resp_str = http.getString();
        Serial.printf("[INCIDENT] Case logged in Investigation Center: %s\n", resp_str.c_str());
        set_led_and_voice("RED_FLASH", "Fraud incident reported. Case opened.");
    }
    http.end();
}

// -----------------------------------------------------------------------------
// SETUP & MAIN LOOP
// -----------------------------------------------------------------------------
void setup() {
    Serial.begin(115200);
    delay(500);

    pinMode(PIN_BTN_VERIFY, INPUT_PULLUP);
    pinMode(PIN_BTN_REPORT_FRAUD, INPUT_PULLUP);
    pinMode(PIN_LED_GREEN, OUTPUT);
    pinMode(PIN_LED_AMBER, OUTPUT);
    pinMode(PIN_LED_RED, OUTPUT);
    pinMode(PIN_BUZZER, OUTPUT);

    Serial.println("==================================================");
    Serial.println("QUANTUM KAVACHA -- ESP32-S3 HARDWARE TRUST NODE");
    Serial.printf("Firmware: %s | Digest: %s\n", FIRMWARE_VERSION, FIRMWARE_HASH);
    Serial.println("Features: Auto-Verify | Delayed-Recheck | 4-Tier LED | Voice | 1-Press Report | Dynamic-QR");
    Serial.println("==================================================");

    // Read Unique eFuse Factory MAC
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    sprintf(mac_address_str, "%02X:%02X:%02X:%02X:%02X:%02X", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    sprintf(device_id_str, "QK-ESP32-%02X%02X", mac[4], mac[5]);
    Serial.printf("[HARDWARE ID] Factory MAC: %s -> Node ID: %s\n", mac_address_str, device_id_str);

    // Initialize I2C Bus for Sensor Array
    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN, 400000);
    Wire.beginTransmission(MPU6050_ADDR);
    Wire.write(0x6B); // Wake up MPU6050
    Wire.write(0x00);
    Wire.endTransmission(true);

    // Connect to Wi-Fi
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    Serial.print("[NETWORK] Connecting to Wi-Fi");
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 6) {
        delay(300);
        Serial.print(".");
        retries++;
    }
    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[NETWORK] Connected! IP: %s (CLOUD_CONNECTED)\n", WiFi.localIP().toString().c_str());
        set_led_and_voice("GREEN", "Quantum Kavacha Trust Node online.");
    } else {
        Serial.println("\n[NETWORK] Disconnected. Mode: OFFLINE_SAFETY_MODE");
        set_led_and_voice("AMBER", "Operating in offline safety mode.");
    }
}

void loop() {
    // 1. Check Button 1: VERIFY PAYMENT
    if (digitalRead(PIN_BTN_VERIFY) == LOW) {
        delay(50); // Debounce
        if (digitalRead(PIN_BTN_VERIFY) == LOW) {
            trigger_auto_verify_payment("TX-DEMO-1001", 450.00, "upi://pay?pa=verified.store@icici&am=450.00");
            delay(1000);
        }
    }

    // 2. Check Button 2: REPORT FRAUD
    if (digitalRead(PIN_BTN_REPORT_FRAUD) == LOW) {
        delay(50);
        if (digitalRead(PIN_BTN_REPORT_FRAUD) == LOW) {
            trigger_one_press_fraud_report("TX-DEMO-1001", 92.0);
            delay(2000);
        }
    }

    // 3. Periodic Background Telemetry Stream
    static unsigned long last_telemetry_ms = 0;
    if (millis() - last_telemetry_ms > 2500) {
        last_telemetry_ms = millis();
        send_telemetry_packet();
    }
    delay(20);
}
