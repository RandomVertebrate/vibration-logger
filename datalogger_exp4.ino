#include "FS.h"
#include "SD.h" // esp32 SD library, not Arduino inbuilt
                // both have the same name
                // possible source of problems?
#include "esp_task_wdt.h"
#include "SPI.h"
#include "src/accelerometer/MPU6050.h"
#include "src/accelerometer/I2Cdev.h"
#include "src/gps/simplegps.h"
#include "src/data/datablock.h"

#define ACCEL_RANGE       MPU6050_ACCEL_FS_8 // (ALSO CHANGE OFFSETS): Full-scale range, options 2g, 4g, 8g and 16g.

#define ACCEL_X_OFFSET    75 // Unit-specific zero error along x-axis in LSBs
#define ACCEL_Y_OFFSET    45 // Unit-specific zero error along x-axis in LSBs
#define ACCEL_Z_OFFSET    540 // Unit-specific zero error along x-axis in LSBs

#define SDA_PIN           GPIO_NUM_21
#define SCL_PIN           GPIO_NUM_22

#define DELIMITER         "thisisadelimiter" // delimiter to write after every datablock
#define DELIMITER_LENGTH  16

File data_log_file;

MPU6050 accel;
simplegps gps;

// struct datablock contains one timeseries and gps data.
datablock main_data;

bool currently_copying_gps_data = 0; // flag to prevent writing datablock to file while datablock is being written to

void get_accel_readings(MPU6050 &a, timeseries &ts)
{
  for (int i = 0; i<TIMESERIES_LENGTH; i++)
  {
    accel.getIntDataReadyStatus(); // reading from the data ready interrupt to reset it to 0
    while(!accel.getIntDataReadyStatus()) // waiting till data is ready
      delayMicroseconds(10);
    
    accel.getAcceleration(&ts.readings[i][0], &ts.readings[i][1], &ts.readings[i][2]);
    ts.readings[i][0] -= ACCEL_X_OFFSET;
    ts.readings[i][1] -= ACCEL_Y_OFFSET;
    ts.readings[i][2] -= ACCEL_Z_OFFSET;
  }
}

void copy_gps_data(datablock &d, simplegps g)
{
  d.date_day = g.date_day;
  d.date_month = g.date_month;
  d.date_year = g.date_year;
  d.date_format = g.date_format;
  d.time_hours = g.time_hours;
  d.time_minutes = g.time_minutes;
  d.time_seconds = g.time_seconds;
  d.time_format = g.time_format;
  d.latitude_degrees = g.latitude_degrees;
  d.latitude_minutes = g.latitude_minutes;
  d.latitude_format = g.latitude_format;
  d.longitude_degrees = g.longitude_degrees;  
  d.longitude_minutes = g.longitude_minutes;
  d.longitude_format = g.longitude_format;
  d.altitude = g.altitude;
  d.altitude_format = g.altitude_format;
}

void setup()
{
  Serial.begin(230400); // Not ultimately needed
  Serial.setDebugOutput(0);
  if (!SD.begin())
      Serial.print("\nSD did not initialize\n");
  accel.initialize(SDA_PIN, SCL_PIN);
  accel.setRate(79); //Sample Rate = 8kHz / (79 + 1) = 100Hz
  accel.setFullScaleAccelRange(ACCEL_RANGE); // set full-scale range
  accel.setIntDataReadyEnabled(1); // enable 'data ready' interrupt so can check whether data is ready to be read
  gps.initialize(9600);

  // set format variables in main_data to null to indicate uninitialized
  main_data.date_format = '\0';
  main_data.time_format = '\0';
  main_data.latitude_format = '\0';
  main_data.longitude_format = '\0';
  main_data.altitude_format = '\0';
}

// Executes as separate task on second processor (core 1)
// setup() and loop() run on core 0
void get_gps_in_parallel(void* dummy)
{
  gps.update_data();

  currently_copying_gps_data = 1;
  copy_gps_data(main_data, gps);
  currently_copying_gps_data = 0;
  
  showaccel(main_data); // Not ultimately needed, function defined in datablock.h
  
  vTaskDelete(NULL); // end task and free processor for next call of this function
}

void loop()
{
  get_accel_readings(accel, main_data.acceldata);

  while(currently_copying_gps_data) // wait for data to finish being copied
    delayMicroseconds(1);
  
  data_log_file = SD.open("/AxGPS.log", FILE_APPEND);  
  data_log_file.write((uint8_t*)&main_data, sizeof(main_data));
  data_log_file.write((uint8_t*)DELIMITER, DELIMITER_LENGTH);
  data_log_file.close();

  // Calling get_gps_in_parallel() as separate task on core 1
  xTaskCreatePinnedToCore(get_gps_in_parallel, "GPSdump", 10000, NULL, 1, NULL,  1);
}
