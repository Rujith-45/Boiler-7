#include <WiFi.h>
#include <ThingSpeak.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ================= LCD =================
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ================= WI-FI CONFIGURATION =================
// Replace with your Wi-Fi credentials
const char* WIFI_SSID = "Rujith's Dell";
const char* WIFI_PASS = "Parimala";

// ================= THINGSPEAK CONFIGURATION =================
const unsigned long myChannelNumber = 3500246;
const char* myWriteAPIKey           = "4MBMDDLPU78NBNF4";

WiFiClient client;

// ================= PIN DEFINITIONS =================
#define FLOW_SENSOR_PIN  4
#define TEMP_PIN         34

// ================= SENSOR VARIABLES =================
volatile unsigned long pulseCount = 0;

float flowRate    = 0.0;
float totalLiters = 0.0;
float currentTemp = 0.0;

// Calibration for common YF-S201
#define PULSES_PER_LITER 450.0

// ================= NON-BLOCKING TIMERS =================
unsigned long previousFlowMillis = 0;
unsigned long previousLcdMillis  = 0;
unsigned long previousTSMillis   = 0;

const unsigned long FLOW_INTERVAL = 1000;   // Calculate flow every 1 sec
const unsigned long LCD_INTERVAL  = 2500;   // Toggle LCD screen every 2.5 sec
const unsigned long TS_INTERVAL   = 15000;  // Push to ThingSpeak every 15 sec (free tier limit)

int lcdScreenState = 0; // 0 = Flow/Temp, 1 = Total Liters

// ================= FLOW SENSOR INTERRUPT =================
void IRAM_ATTR pulseCounter()
{
  pulseCount++;
}

// ================= HELPER: READ TEMPERATURE =================
float readTemperature()
{
  float raw = analogRead(TEMP_PIN);
  float t = 500.0 * (raw / 1023.0);
  if (t > 0.001 && (5.0 / t - 1.0) != 0.0) {
    t = 100.0 / ((5.0 / t - 1.0) * 3.9);
    return 60.0 + t;
  }
  return 0.0;
}

// ================= SETUP =================
void setup()
{
  Serial.begin(115200);

  // Flow sensor pin with internal pullup
  pinMode(FLOW_SENSOR_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(FLOW_SENSOR_PIN), pulseCounter, FALLING);

  // I2C LCD on ESP32 default SDA=21, SCL=22
  Wire.begin(21, 22);
  lcd.init();
  lcd.backlight();
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("FLOW + PT100");
  lcd.setCursor(0, 1);
  lcd.print("CONNECTING WIFI");

  // Connect to Wi-Fi
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  lcd.clear();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected! IP: " + WiFi.localIP().toString());
    lcd.setCursor(0, 0);
    lcd.print("WiFi Connected!");
    lcd.setCursor(0, 1);
    lcd.print("ThingSpeak Ready");
  } else {
    Serial.println("\nWiFi connection failed! Continuing offline...");
    lcd.setCursor(0, 0);
    lcd.print("WiFi Failed!");
    lcd.setCursor(0, 1);
    lcd.print("Running Local...");
  }

  delay(2000);
  lcd.clear();

  // Initialize ThingSpeak
  ThingSpeak.begin(client);

  previousFlowMillis = millis();
  previousLcdMillis  = millis();
  previousTSMillis   = millis();
}

// ================= LOOP =================
void loop()
{
  unsigned long currentMillis = millis();

  // -------------------------------------------------------------
  // 1. FLOW & TEMPERATURE CALCULATION (EVERY 1 SECOND)
  // -------------------------------------------------------------
  if (currentMillis - previousFlowMillis >= FLOW_INTERVAL)
  {
    // Atomically retrieve and reset pulse counter
    noInterrupts();
    unsigned long pulses = pulseCount;
    pulseCount = 0;
    interrupts();

    // Flow calculations
    float litersPerSecond = pulses / PULSES_PER_LITER;
    flowRate = litersPerSecond * 60.0;    // L/min
    totalLiters += litersPerSecond;       // Cumulative liters

    // Read temperature
    currentTemp = readTemperature();

    previousFlowMillis = currentMillis;

    // Serial monitor debugging
    Serial.print("Flow: ");
    Serial.print(flowRate, 2);
    Serial.print(" L/min | Temp: ");
    Serial.print(currentTemp, 2);
    Serial.print(" C | Total: ");
    Serial.print(totalLiters, 3);
    Serial.println(" L");
  }

  // -------------------------------------------------------------
  // 2. LCD SCREEN ALTERNATION (NON-BLOCKING EVERY 2.5 SECONDS)
  // -------------------------------------------------------------
  if (currentMillis - previousLcdMillis >= LCD_INTERVAL)
  {
    previousLcdMillis = currentMillis;
    lcdScreenState = !lcdScreenState; // Toggle between Screen 0 and 1

    if (lcdScreenState == 0)
    {
      // Screen 1: Flow & Temp
      lcd.setCursor(0, 0);
      lcd.print("Flow: ");
      lcd.print(flowRate, 1);
      lcd.print(" L/m   ");

      lcd.setCursor(0, 1);
      lcd.print("Temp: ");
      lcd.print(currentTemp, 1);
      lcd.print((char)223);
      lcd.print("C   ");
    }
    else
    {
      // Screen 2: Total Water & Cloud Status
      lcd.setCursor(0, 0);
      lcd.print("Total Water:    ");

      lcd.setCursor(0, 1);
      lcd.print(totalLiters, 2);
      lcd.print(" Liters ");
    }
  }

  // -------------------------------------------------------------
  // 3. PUSH TO THINGSPEAK (EVERY 15 SECONDS)
  // -------------------------------------------------------------
  if (currentMillis - previousTSMillis >= TS_INTERVAL)
  {
    previousTSMillis = currentMillis;

    if (WiFi.status() == WL_CONNECTED)
    {
      Serial.println("\n[ThingSpeak] Uploading telemetry...");

      ThingSpeak.setField(1, flowRate);     // Field 1: Flow (L/min)
      ThingSpeak.setField(2, currentTemp);  // Field 2: Temperature (deg C)
      ThingSpeak.setField(3, totalLiters);  // Field 3: Total Water (L)

      int status = ThingSpeak.writeFields(myChannelNumber, myWriteAPIKey);

      if (status == 200) {
        Serial.println("[ThingSpeak] Upload SUCCESS (HTTP 200)");
      } else {
        Serial.print("[ThingSpeak] Upload ERROR! HTTP code: ");
        Serial.println(status);
      }
    }
    else
    {
      Serial.println("[WiFi] Reconnecting...");
      WiFi.reconnect();
    }
  }
}
