#include "Secrets.h"
#include "SparkFunLIS3DH.h"
#include "MAX30105.h"
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
/*extern "C" {
#include "user_interface.h"
}  */

LIS3DH myIMU; // constructed with parameters for SPI and cs pin number
MAX30105 particleSensor;
int counter = 0;
unsigned long startTime;
const int CHUNK_SIZE = 100; //50 samples / sec * 60 sec = 3000 samples = 3kb
const int BITS_OF_DATA = 32;
//String data[CHUNK_SIZE];
char data[CHUNK_SIZE*BITS_OF_DATA+1];

void connectWifi()
{
    WiFi.begin(ssid, wifipasswd);
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

void postServer(String postMesg)
{
    if (WiFi.status() != WL_CONNECTED){
        Serial.println("WIFI Error");
        return;
    }
    HTTPClient http;
    Serial.println("[HTTP] begin");
    http.begin("http://13.57.112.90/sensor_b64.php/"); //HTTP
    //http.begin("http://192.168.43.224/~ryansun1/embed/sensor_b64.php/"); //HTTP

    digitalWrite(LED_BUILTIN, LOW);
    Serial.println("[HTTP] POST");

    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    Serial.println(postMesg);        
    int httpCode = http.POST(postMesg); 

    if(httpCode > 0) {
        Serial.printf("[HTTP] POST code: %d\n", httpCode);
        if(httpCode == HTTP_CODE_OK) {
            String payload = http.getString();
            Serial.println(payload);
        }
    } else {
        Serial.printf("[HTTP] POST failed, error: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();
    digitalWrite(LED_BUILTIN, HIGH);
}

/*
void read_sensor(float * x, float * y, float * z, int * IR, int * RED) {
    *x = myIMU.readFloatAccelX();
    *y = myIMU.readFloatAccelY();
    *z = myIMU.readFloatAccelZ();
    *IR = particleSensor.getIR();
    *RED = particleSensor.getRed();
}
*/
void print_sensor(float & x, float & y, float & z, int & IR, int & RED) {
    Serial.println("\nAccelerometer:");
    Serial.print(" X = ");
    Serial.println(x, 4);
    Serial.print(" Y = ");
    Serial.println(y, 4);
    Serial.print(" Z = ");
    Serial.println(z, 4);
    Serial.println("\nPPG:");
    Serial.print(" IR = ");
    Serial.println(IR, 4);
    Serial.print(" RED = ");
    Serial.println(RED, 4);
}

void startPPGSensor()
{
    // Initialize sensor
    if (!particleSensor.begin(Wire, I2C_SPEED_FAST)) //Use default I2C port, 400kHz speed
    {
        Serial.println("MAX30105 was not found. Please check wiring/power. ");
        while (1);
    }
    
    particleSensor.setup(); //Configure sensor. Use 6.4mA for LED drive
    particleSensor.setSampleRate(50);  //set freq = 50
    particleSensor.setFIFOAverage(0x10);
}

String to_JSON_data(char * data, int len) {
    String s;
    char tmp[BITS_OF_DATA+1];
    for(int j = 0; j < BITS_OF_DATA+1; j++){
        tmp[j] = '\0';
    }

    //s = "data={\"sensor\":[\"";
    s = "data=[\"";
    for(int i = 0; i < len-1; i++){
        for(int j = 0; j < BITS_OF_DATA; j++){
            tmp[j] = data[i*BITS_OF_DATA + j];
        }
        s += tmp;
        s += "\",\"";
    }
    for(int j = 0; j < BITS_OF_DATA; j++){
        tmp[j] = data[(len-1)*BITS_OF_DATA + j];
    }
    s += tmp;
    s += "\"]}";
    return s;
    
    /*
    String s;
    s = "data={\"sensor\":[";
    for(int i = 0; i < len-1; i++){
        s += data[i] + ",";
    }
    s += data[len-1] + "]}";
    return s;
    */
}

/*
String to_JSON_array(float & x, float & y, float & z, int & IR, int & RED){
    String s = "[" + String(x,'\005') + "," +String(y, '\005') + "," + String(z, '\005') + "," + String(IR) + "," + String(RED) + "]";
    return s;
}
*/
void setup() {
    // put your setup code here, to run once:
    Serial.begin(115200);
    delay(1000); //relax...
    Serial.println("Processor came out of reset.\n");
    digitalWrite(LED_BUILTIN, LOW);
    //Call .begin() to configure the IMU

    connectWifi();
    myIMU.begin();
    startPPGSensor();
    digitalWrite(LED_BUILTIN, HIGH);
    pinMode(LED_BUILTIN, OUTPUT);
    delay(1000);
    startTime = millis();
    for(int i = 0; i < CHUNK_SIZE*BITS_OF_DATA+1; i++){
        data[i] = '\0';
    }
}
void base64Encode(char * s, uint32_t x, uint32_t y, uint32_t z){
    uint64_t yz = ((uint64_t)y << (sizeof(uint32_t) * 8)) | z;
    //char * s = (char *)malloc(16*sizeof(char)+1);
    for(int i = 15; i >= 0; i--){
        char tmp = yz & 0x003F;
        if (tmp < 26){
            s[i] = 'A' + tmp;
        }
        else if (tmp < 52){
            s[i] = 'a' + (tmp - 26);
        }
        else if (tmp < 62){
            s[i] = '0' + (tmp - 52);
        }
        else if (tmp == 62){
            s[i] = '+';
        }
        else{
            s[i] = '/';
        }
        yz >>= 6;
        //encoded 60 bits of yz, only 4 bits remain
        //now, load x into yz, so 32+4=36 bits available
        if (i == 6){
            yz |= (uint64_t)x << 4;
        }
        //s[16] = '\0';
    }
    //return s;
}

void loop()
{
     //Get all parameters
    //float x[CHUNK_SIZE],y[CHUNK_SIZE],z[CHUNK_SIZE];
    //Serial.println(st);
    //free(st);
    delay(10000);
    float x, y, z;
    int IR, RED;
    for(int i = 0; i < CHUNK_SIZE; i++){
        delay(10);
        base64Encode(data + i * BITS_OF_DATA, 
            myIMU.readRawAccelX(), myIMU.readRawAccelY(), myIMU.readRawAccelZ());
        base64Encode(data + i * BITS_OF_DATA + BITS_OF_DATA/2, 
            0, particleSensor.getIR(), particleSensor.getRed());        
        //read_sensor(&x,&y,&z,&IR,&RED);
        //print_sensor(x,y,z,IR,RED);
        //data[i] = to_JSON_array(x, y, z, IR, RED);
        Serial.println(counter);
        counter++;
    }
    String s = to_JSON_data(data, CHUNK_SIZE);
    postServer(s);
    if (counter > 10 * CHUNK_SIZE){
        delay(100 * 1000);
    }
    if((millis() - startTime) > 10 * 60* 1000)   //set 10 minutes
    {
        digitalWrite(LED_BUILTIN, LOW);
        //uint32_t free = system_get_free_heap_size();      //see the remaining size of heap
        //Serial.println(free);
        delay(500000000);
    }
}