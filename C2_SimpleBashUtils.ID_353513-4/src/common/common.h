#ifndef COMMON_H
#define COMMON_H

#include <stdlib.h>

// Function to duplicate a string
char *my_strdup(const char *str);

// Function to add a string to a dynamic array
void add_string(char ***list, int *count, const char *new_string);

#endif  // COMMON_H
