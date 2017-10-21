#include <Wire.h>
#include "MAX30105.h"
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

MAX30105 particleSensor;
unsigned long startTime;
// WiFi settings
const char *ssid = "UCInet Mobile Access";

void connectWifi()
{
    WiFi.begin(ssid);//, wifipasswd);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println("");
    Serial.println("WiFi connected");
    // Print the IP address
    Serial.println(WiFi.localIP());
}

void postServer(String postMesg, int powerLevel)
{
    String data;
    data = "data={\"powerLevel\": "+String(powerLevel)+", \"data\": ["+postMesg+"]}";

    if (WiFi.status() != WL_CONNECTED){
        Serial.println("WIFI Error");
        return;
    }
        HTTPClient http;
        Serial.print("[HTTP] begin...\n");
        http.begin("http://13.57.112.90/writeCSV.php/"); //HTTP
        
        digitalWrite(LED_BUILTIN, LOW);
        Serial.print("[HTTP] POST...\n");

        http.addHeader("Content-Type", "application/x-www-form-urlencoded");
        Serial.println(data);        
        int httpCode = http.POST(data); 

        if(httpCode > 0) {
            Serial.printf("[HTTP] POST... code: %d\n", httpCode);
            if(httpCode == HTTP_CODE_OK) {
                String payload = http.getString();
                Serial.println(payload);
            }
        } else {
            Serial.printf("[HTTP] POST... failed, error: %s\n", http.errorToString(httpCode).c_str());
        }
        http.end();
        digitalWrite(LED_BUILTIN, HIGH);
}


void startSensor(int powerLevel)
{
    // Initialize sensor
    if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) //Use default I2C port, 400kHz speed
    {
      Serial.println("MAX30105 was not found. Please check wiring/power. ");
      while (1);
    }
    particleSensor.setup(); //Configure sensor. Use 6.4mA for LED drive

    particleSensor.setPulseAmplitudeRed(powerLevel);
    particleSensor.setPulseAmplitudeIR(powerLevel);
    particleSensor.setPulseAmplitudeGreen(powerLevel);
    particleSensor.setPulseAmplitudeProximity(powerLevel);
    particleSensor.setSampleRate(50);  //set freq = 50
}

void captureData()
{
  int powerLevel[4] = {0x02,0x1F,0x7F,0xFF};   //0.4mA, 6.4mA, 25.4mA,  50.0mA
  for(int i=0;i<4;i++){
    String data = "";
    int count = 0;
    
    //delay(1000);

    startTime = millis();
    startSensor(powerLevel[i]); 
    while (1){
      data += "[";
      data += particleSensor.getIR();
      data += ",";
      data += particleSensor.getRed();
      data += "]";

      Serial.print(" R[");
      Serial.print(particleSensor.getRed());
      Serial.print("] IR[");
      Serial.print(particleSensor.getIR());
      
      Serial.print("  powerLevel = ");
      Serial.print(i);
      Serial.println();

      if((millis() - startTime) > 120000)   //set 2 minutes
        break;
    
      count++;
      if (count == 20){         //post to server after every twenty data captured
        postServer(data,i+1);    //i is for powerlevel, for seperating different cvs
        count = 0;
        data = "";
      }
      else
        data += ",";
    }
    postServer(data,i+1);
  }
}

void setup()
{
  Serial.begin(115200);
  Serial.println("Initializing...");
  connectWifi();
  captureData();
}

void loop()
{
}
