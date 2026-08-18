#include "s21_cat.h"

#define MAX_LINE_LENGTH 1024

int main(int argc, char *argv[]) {
  int status = openFile(argv, argc);
  return status;
}

int openFile(char **options, int countOp) {
  char *filename = "";
  int modeMB = 0;
  int modeME = 0;
  int modeMN = 0;
  int modeMS = 0;
  int modeMT = 0;

  for (int i = 1; i < countOp; i++) {
    if (strcmp(options[i], "-b") == 0 ||
        strcmp(options[i], "--number-nonblank") == 0) {
      modeMB++;
    } else if (strcmp(options[i], "-e") == 0 || strcmp(options[i], "-E") == 0) {
      modeME++;
    } else if (strcmp(options[i], "-n") == 0 ||
               strcmp(options[i], "--number") == 0) {
      modeMN++;
    } else if (strcmp(options[i], "-s") == 0 ||
               strcmp(options[i], "--squeeze-blank") == 0) {
      modeMS++;
    } else if (strcmp(options[i], "-t") == 0 || strcmp(options[i], "-T") == 0) {
      modeMT++;
    } else if (options[i][0] != '-') {
      filename = options[i];
    }
  }

  FILE *filePointer = fopen(filename, "r");
  if (filePointer == NULL) {
    printf("Error opening file: %s\n", filename);
    return 0;
  }

  printFile(filePointer, modeMB, modeME, modeMN, modeMS, modeMT);
  fclose(filePointer);
  return 1;
}

int printFile(FILE *filePointer, int modeMB, int modeME, int modeMN, int modeMS,
              int modeMT) {
  char line[MAX_LINE_LENGTH];
  int lineLength = 1;
  int isBeforeLineEmpty = 0;

  while (fgets(line, sizeof(line), filePointer) != NULL) {
    int isEmpty = 1;

    for (int i = 0; line[i] != '\0'; i++) {
      if (!isspace(line[i])) {
        isEmpty = 0;
        break;
      }
    }

    if (modeMB == 1 && isEmpty == 0) {
      printf("%6d\t", lineLength);
      lineLength++;
    } else if (modeMN == 1) {
      printf("%6d\t", lineLength);
      lineLength++;
    }

    if (!(isBeforeLineEmpty == 1 && isEmpty == 1 && modeMS == 1)) {
      for (size_t i = 0; i < strlen(line); i++) {
        if (line[i] == '\t' && modeMT == 1) {
          printf("^I");
        } else if (line[i] == '\n' && modeME == 1) {
          printf("$\n");
        } else {
          printf("%c", line[i]);
        }
      }
      if (modeME == 1 && line[strlen(line) - 1] != '\n') {
        printf("$");
      }
    }
    isBeforeLineEmpty = isEmpty;
  }
  return 0;
}
