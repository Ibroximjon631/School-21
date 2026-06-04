#ifndef S21_GREP_H
#define S21_GREP_H

#include <ctype.h>
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../common/common.h"

void add_string(char ***list, int *count, const char *new_string);
int searching(int argc, char *argv[]);
int searchingInFile(const char *fileName, FILE *filePointer, char **options,
                    int countOp, char **patterns, int countPatterns,
                    int multipleFiles);
void printErrorMessage(const char *name);
int isDirectory(const char *path);

#endif
