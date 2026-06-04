#include "s21_grep.h"

int main(int argc, char *argv[]) {
  searching(argc, argv);
  return EXIT_SUCCESS;
}

int searching(int count, char *argv[]) {
  char **options = NULL;
  int countOp = 0;
  int optionE = 0;
  char **patternsE = NULL;
  char **nameFiles = NULL;
  int countFile = 0;
  int patternSpecified = 0;

  for (int i = 1; i < count; i++) {
    if (argv[i][0] == '-' && strcmp(argv[i], "-e") != 0) {
      add_string(&options, &countOp, argv[i]);
    } else if (strcmp(argv[i], "-e") == 0) {
      if (i + 1 < count) {
        add_string(&patternsE, &optionE, argv[i + 1]);
        i++;
        patternSpecified = 1;
      } else {
        fprintf(stderr, "Option -e requires an argument\n");
        exit(EXIT_FAILURE);
      }
    } else if (!patternSpecified) {
      add_string(&patternsE, &optionE, argv[i]);
      patternSpecified = 1;
    } else {
      add_string(&nameFiles, &countFile, argv[i]);
    }
  }

  if (countFile == 0) {
    fprintf(stderr, "No files specified\n");
    exit(EXIT_FAILURE);
  }

  int multipleFiles = (countFile > 1);

  for (int i = 0; i < countFile; i++) {
    if (isDirectory(nameFiles[i])) {
      printErrorMessage(nameFiles[i]);
    } else {
      FILE *file = fopen(nameFiles[i], "r");
      if (file != NULL) {
        if (searchingInFile(nameFiles[i], file, options, countOp, patternsE,
                            optionE, multipleFiles) == 1) {
          printf("%s\n", nameFiles[i]);
        }
        fclose(file);
      } else {
        fprintf(stderr, "No such file: %s\n", nameFiles[i]);
        exit(EXIT_FAILURE);
      }
    }
  }

  for (int i = 0; i < countOp; i++) {
    free(options[i]);
  }
  for (int i = 0; i < optionE; i++) {
    free(patternsE[i]);
  }
  free(options);
  free(patternsE);
  for (int i = 0; i < countFile; i++) {
    free(nameFiles[i]);
  }
  free(nameFiles);

  return 0;
}

void printErrorMessage(const char *name) {
  fprintf(stderr, "grep: %s: Is a directory\n", name);
}

int isDirectory(const char *path) {
  DIR *directory = opendir(path);
  if (directory != NULL) {
    closedir(directory);
    return 1;
  }
  return 0;
}

int caseInsensitiveStrstr(const char *haystack, const char *needle) {
  if (!*needle) {
    return 1;
  }

  for (; *haystack; ++haystack) {
    if (tolower(*haystack) == tolower(*needle)) {
      const char *h, *n;
      for (h = haystack, n = needle; *h && *n; ++h, ++n) {
        if (tolower(*h) != tolower(*n)) {
          break;
        }
      }
      if (!*n) {
        return 1;
      }
    }
  }
  return 0;
}
int searchingInFile(const char *fileName, FILE *filePointer, char **options,
                    int countOptions, char **patterns, int countPatterns,
                    int multipleFiles) {
  int optionI = 0;
  int optionV = 0;
  int optionC = 0;
  int optionL = 0;
  int optionN = 0;

  for (int i = 0; i < countOptions; i++) {
    if (strcmp(options[i], "-i") == 0) {
      optionI = 1;
    } else if (strcmp(options[i], "-v") == 0) {
      optionV = 1;
    } else if (strcmp(options[i], "-c") == 0) {
      optionC = 1;
    } else if (strcmp(options[i], "-l") == 0) {
      optionL = 1;
    } else if (strcmp(options[i], "-n") == 0) {
      optionN = 1;
    }
  }

  char line[1024];
  int lineNum = 0;
  int matchCount = 0;

  while (fgets(line, sizeof(line), filePointer) != NULL) {
    lineNum++;
    int found = 0;
    for (int i = 0; i < countPatterns; i++) {
      if (optionI) {
        found = caseInsensitiveStrstr(line, patterns[i]);
      } else {
        found = (strstr(line, patterns[i]) != NULL);
      }
      if (found) break;
    }
    if ((found && !optionV) || (!found && optionV)) {
      if (optionL) {
        return 1;
      }
      matchCount++;
      if (!optionC) {
        if (multipleFiles) {
          if (optionN) {
            printf("%s:%d:", fileName, lineNum);
          } else {
            printf("%s:", fileName);
          }
        } else if (optionN) {
          printf("%d:", lineNum);
        }
        printf("%s", line);
      }
    }
  }

  if (optionC) {
    if (multipleFiles) {
      printf("%s:", fileName);
    }
    printf("%d\n", matchCount);
  }

  return 0;
}
