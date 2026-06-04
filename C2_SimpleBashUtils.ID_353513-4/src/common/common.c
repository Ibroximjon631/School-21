#include "common.h"

#include <stdio.h>
#include <string.h>

char *my_strdup(const char *str) {
  size_t len = strlen(str) + 1;
  void *new = malloc(len);
  if (new == NULL) return NULL;
  return (char *)memcpy(new, str, len);
}

void add_string(char ***list, int *count, const char *new_string) {
  *list = (char **)realloc(*list, (*count + 1) * sizeof(char *));
  if (*list == NULL) {
    fprintf(stderr, "Memory reallocation failed\n");
    exit(EXIT_FAILURE);
  }
  (*list)[*count] = my_strdup(new_string);
  if ((*list)[*count] == NULL) {
    fprintf(stderr, "Memory allocation for string failed\n");
    exit(EXIT_FAILURE);
  }
  (*count)++;
}
