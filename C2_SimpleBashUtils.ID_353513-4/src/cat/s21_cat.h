#ifndef S21_CAT_H
#define S21_CAT_H

#include <ctype.h>
#include <stdio.h>
#include <string.h>

#include "../common/common.h"

int openFile(char **options, int countOp);
int printFile(FILE *filePointer, int modeMB, int modeME, int modeMN, int modeMS,
              int modeMT);

#endif
