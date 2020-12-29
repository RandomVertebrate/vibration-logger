#include <stdint.h>
#define TIMESERIES_LENGTH 300 // 300 readings at a time
#define TIMESERIES_WIDTH  3   // for x, y, and z

struct timeseries
{
  int16_t readings[TIMESERIES_LENGTH][TIMESERIES_WIDTH];
};

struct datablock
{
  // assuming double 8 bytes
  timeseries acceldata;
  uint8_t date_day;
  uint8_t date_month;
  uint8_t date_year;
  char date_format;
  uint8_t time_hours;
  uint8_t time_minutes;
  double time_seconds;
  char time_format;
  uint8_t latitude_degrees;
  double latitude_minutes;
  char latitude_format;
  uint8_t longitude_degrees;
  double longitude_minutes;
  char longitude_format;
  double altitude;
  char altitude_format;
};

// show() function not ultimately needed
void show(datablock &d)
{
  for (int i = 0; i<TIMESERIES_LENGTH; i++)
  {
    for (int j = 0; j<TIMESERIES_WIDTH; j++)
    {
      Serial.print(d.acceldata.readings[i][j]); Serial.print(' ');
    }
    Serial.print('\n');
  }
  Serial.print("Date... ");
  Serial.print(d.date_day); Serial.print("/"); Serial.print(d.date_month); Serial.print("/"); Serial.print(d.date_year); Serial.print(d.date_format); Serial.print("\n");
  Serial.print("Time... ");
  Serial.print(d.time_hours); Serial.print(":"); Serial.print(d.time_minutes); Serial.print(":"); Serial.print(d.time_seconds); Serial.print("\n");
  Serial.print("Latitude... ");
  Serial.print(d.latitude_degrees); Serial.print("*"); Serial.print(d.latitude_minutes); Serial.print("'"); Serial.print(d.latitude_format); Serial.print("\n");
  Serial.print("Longitude... ");
  Serial.print(d.longitude_degrees); Serial.print("*"); Serial.print(d.longitude_minutes); Serial.print("'"); Serial.print(d.longitude_format); Serial.print("\n");
  Serial.print("Altitude... ");
  Serial.print(d.altitude); Serial.print(d.altitude_format); Serial.print("\n\n");
}
