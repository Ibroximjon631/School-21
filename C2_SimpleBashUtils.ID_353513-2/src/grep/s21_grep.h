#include <stdio.h>

#include "getopt.h"
#include "regex.h"
#include "stdlib.h"
#include "string.h"

typedef struct use_flags {
  int e;
  int i;
  int v;
  int c;
  int l;
  int n;
  int h;
  int s;
  int f;
  int o;
} use_flags;

void parser_flags(int argc, char **argv, use_flags *flags, char *regexp);
void print_file(int argc, char **argv, use_flags *flags, char *regexp);
int read_file(char *regexp, char *name);
void find_regexp(use_flags *flags, char *regexp, char *file, int count_files);
void grep(use_flags *flags, FILE *f, regex_t *comp_regexp, char *file_name,
          int count_files);
void flags_l_c(use_flags *flags, int line_matches, char *file_name,
               int count_files);
void flag_n(use_flags *flags, int count_files, char *file_name, int number_line,
            char *text);
void flag_v(use_flags *flags, int count_files, char *file_name, char *text);
void flag_o(use_flags *flags, int count_files, char *file_name, int number_line,
            regmatch_t *one_match, char *text);