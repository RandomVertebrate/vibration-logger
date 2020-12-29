#include "simplegps.h"


// function compares first n characters of a character array against passed string
bool compare_n_chars(char *a, const char* b, int n)
{
  for (int i = 0; i<n; i++)
      if (a[i] != b[i])
          return 0;
  return 1;
}

// converts first n characters of a character array to a number
double numeric(char str[], int n)
{
    char* buf = new char[n+1];
    for (int i = 0; i<n; i++)
        buf[i] = str[i];
    buf[n] = '\0';
    char* endptr;
    return strtod(buf, &endptr);
}

void simplegps::getsentence()
  {
    char current;

    while (Serial2.read()!='$');

    int i;
    for (i = 0; i<SENTENCE_BUFFER_SIZE; i++)
        {
          while(!Serial2.available()); // Wait for available: Seems inefficient but I don't know enough to know how inefficient.
          current = Serial2.read();
          if (current == '\n')
              {
                sentence[i] = '\0';
                sentence_length = i;
                return;
              }
          sentence[i] = current;
        }
    sentence_length = i;
  }

void simplegps::getwords()
  {
    // initialize lengths to 0
    for(int i=0; i<50; i++)
        word_length[i] = 0;

    int current_word_index = 0;

    word_ptrs[0] = (char*)sentence; // first word starts at beginning of sentence

    for (int i = 0, j = 0; i < SENTENCE_BUFFER_SIZE - 1; i++, j++)
        {
          if (sentence[i] == '\0')
              {
                word_length[current_word_index] = j;
                no_of_words = current_word_index + 1;
                return;
              }
          if (sentence[i] == ',')
              {
                word_length[current_word_index] = j;
                j = -1;                                                 // will be set to zero on next iteration
                current_word_index++;
                word_ptrs[current_word_index] = (char*)&sentence[i+1];
              }
        }

    no_of_words = current_word_index + 1;
  }

void simplegps::readLOC()
  {
     getwords(); // set pointers to beginnings of each word of sentence[] in word_ptrs[] and set word lengths in word_length[].

     // check if each word is empty, if not convert to appr. type and store in public vars. If empty assign zero.
     if (word_length[TIME_WORD] == 0)
         {
              time_hours = time_minutes = time_seconds = 0;
              time_format = '\0'; // Allows checking for time reading availability during file parse
         }
     else
         {
              time_hours = (int)numeric(word_ptrs[TIME_WORD], TIME_MINUTES_CHAR - TIME_HOURS_CHAR);
              time_minutes = (int)numeric(word_ptrs[TIME_WORD] + TIME_MINUTES_CHAR, TIME_SECONDS_CHAR - TIME_MINUTES_CHAR);
              time_seconds = numeric(word_ptrs[TIME_WORD] + TIME_SECONDS_CHAR, word_length[TIME_WORD] - TIME_SECONDS_CHAR);
              time_format = 'U'; // Allows checking for time reading availability during file parse
         }

     if (word_length[LATITUDE_WORD] == 0)
         latitude_degrees = latitude_minutes = 0;
     else
         {
              latitude_degrees = (int)numeric(word_ptrs[LATITUDE_WORD], LATITUDE_MINUTES_CHAR - LATITUDE_DEGREES_CHAR);
              latitude_minutes = numeric(word_ptrs[LATITUDE_WORD] + LATITUDE_MINUTES_CHAR, word_length[LATITUDE_WORD] - LATITUDE_MINUTES_CHAR);
         }

     if (word_length[LONGITUDE_WORD] == 0)
         longitude_degrees = longitude_minutes = 0;
     else
         {
              longitude_degrees = (int)numeric(word_ptrs[LONGITUDE_WORD], LONGITUDE_MINUTES_CHAR - LONGITUDE_DEGREES_CHAR);
              longitude_minutes = numeric(word_ptrs[LONGITUDE_WORD] + LONGITUDE_MINUTES_CHAR, word_length[LONGITUDE_WORD] - LONGITUDE_MINUTES_CHAR);
         }

     if (word_length[ALTITUDE_WORD] == 0)
         altitude = 0;
     else
         {
              altitude = numeric(word_ptrs[ALTITUDE_WORD], word_length[ALTITUDE_WORD]);
         }

     if (word_length[ALTITUDE_FORMAT_WORD] == 0)
         altitude_format = '\0';
     else
         {
              altitude_format = word_ptrs[ALTITUDE_FORMAT_WORD][0];
         }

     if (word_length[LATITUDE_FORMAT_WORD] == 0)
         latitude_format = '\0';
     else
         {
              latitude_format = word_ptrs[LATITUDE_FORMAT_WORD][0];
         }

     if (word_length[LONGITUDE_FORMAT_WORD] == 0)
         longitude_format = '\0';
     else
         {
              longitude_format = word_ptrs[LONGITUDE_FORMAT_WORD][0];
         }
  }

void simplegps::readDATE()
  {
     getwords(); // set pointers to beginnings of each word of sentence[] in word_ptrs[] and set word lengths in word_length[].

     // check if each word is empty, if not convert to appr. type and store in public vars. If empty assign zero.
     if (word_length[DATE_WORD] == 0)
         {
              date_day = date_month = date_year = 0;
              date_format = '\0'; // Allows checking for time reading availability during file parse
         }
     else
         {
              date_day = (int)numeric(word_ptrs[DATE_WORD], DATE_MONTH_CHAR - DATE_DAY_CHAR);
              date_month = (int)numeric(word_ptrs[DATE_WORD] + DATE_MONTH_CHAR, DATE_YEAR_CHAR - DATE_MONTH_CHAR);
              date_year = (int)numeric(word_ptrs[DATE_WORD] + DATE_YEAR_CHAR, word_length[DATE_WORD] - DATE_YEAR_CHAR);
              date_format = 'D'; // Allows checking for time reading availability during file parse
         }

  }

void simplegps::initialize(int baud_rate)
  {
    Serial2.begin(9600);
    date_day = date_month = date_year = 0;
    time_hours = time_minutes = latitude_degrees = longitude_degrees = 0;
    time_seconds = latitude_minutes = longitude_minutes = altitude = 0.0;
    date_format = time_format = latitude_format = longitude_format = altitude_format = '\0';
  }

void simplegps::update_data()
  {
     // read sentences until we get the one that starts with GPGCA
     while(1)
         {
             getsentence();
             if (compare_n_chars((char*)sentence, LOC_SENTENCE_ID, 5))
                 {
                     readLOC();
                     getsentence();
                     while (!compare_n_chars((char*)sentence, DATE_SENTENCE_ID, 5))
                        getsentence();
                     readDATE();
                     return;
                 }
             else if (compare_n_chars((char*)sentence, DATE_SENTENCE_ID, 5))
                 {
                     readDATE();
                     getsentence();
                     while (!compare_n_chars((char*)sentence, LOC_SENTENCE_ID, 5))
                        getsentence();
                     readLOC();
                     return;
                 }
         }
  }
