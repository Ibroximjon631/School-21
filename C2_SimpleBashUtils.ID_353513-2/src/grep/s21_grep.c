#include "s21_grep.h"

int main(int argc, char **argv) {
  use_flags flags = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
  char regexp[4096] = {0};
  parser_flags(argc, argv, &flags, regexp);

  if (argc >= 3) {
    print_file(argc, argv, &flags, regexp);
  }
  return 0;
}

void parser_flags(int argc, char **argv, use_flags *flags, char *regexp) {
  int opt;

  while ((opt = getopt(argc, argv, "e:ivclnhsf:o")) != -1) {
    if (opt == 'e') {
      flags->e = 1;
      if (*regexp != '\0') {
        strcat(regexp, "|");
      }
      strcat(regexp, optarg);
    }
    if (opt == 'i') flags->i = 1;
    if (opt == 'v') flags->v = 1;
    if (opt == 'c') flags->c = 1;
    if (opt == 'l') flags->l = 1;
    if (opt == 'n') flags->n = 1;
    if (opt == 'h') flags->h = 1;
    if (opt == 's') flags->s = 1;
    if (opt == 'f') {
      flags->f = 1;
      read_file(regexp, optarg);
    }
    if (opt == 'o') flags->o = 1;
  }
}

void print_file(int argc, char **argv, use_flags *flags, char *regexp) {
  if (!flags->f && !flags->e) sprintf(regexp, "%s", argv[optind++]);
  int count_files = argc - optind;
  for (int i = optind; i < argc; i++) {
    // исключаем v + o, они перекрывают друг друга, если нет с или l
    if ((flags->v && flags->o && (flags->c || flags->l)) ||
        !(flags->v && flags->o)) {
      find_regexp(flags, regexp, argv[i], count_files);
    }
  }
}

int read_file(char *regexp, char *name) {
  FILE *f = fopen(name, "r");
  if (*regexp != '\0') {
    strcat(regexp, "|");
  }
  int position = strlen(regexp);
  if (f != NULL) {
    int c;
    while ((c = fgetc(f)) != EOF) {
      if (c == 13 || c == 10) regexp[position++] = '|';
      if (c != 13 && c != 10) regexp[position++] = c;
    }

    if (regexp[position - 1] == '|') regexp[position - 1] = '\0';
    fclose(f);
  }
  return position + 1;
}

void find_regexp(use_flags *flags, char *regexp, char *file, int count_files) {
  int comp_flags = (flags->i) ? REG_ICASE | REG_EXTENDED : REG_EXTENDED;
  regex_t comp_regexp;
  FILE *f = fopen(file, "r");
  if (f != NULL) {
    regcomp(&comp_regexp, regexp, comp_flags);
    grep(flags, f, &comp_regexp, file, count_files);
    regfree(&comp_regexp);
    fclose(f);
  }
}

void grep(use_flags *flags, FILE *f, regex_t *comp_regexp, char *file_name,
          int count_files) {
  char text[4097] = {0};
  regmatch_t one_match[1];
  int line_matches = 0, number_line = 1;

  while (fgets(text, 4096 - 1, f) != NULL) {
    int status = regexec(comp_regexp, text, 1, one_match, 0);
    int match = 0;
    int len = strlen(text);
    if (text[len - 1] != '\n') {
      text[len] = '\n';
      text[len + 1] = '\0';
    }
    if (status == 0 && !flags->v) match = 1;
    if (status == REG_NOMATCH && flags->v) match = 1;
    if (match) {
      flag_n(flags, count_files, file_name, number_line, text);
      flag_v(flags, count_files, file_name, text);
      flag_o(flags, count_files, file_name, number_line, one_match, text);
    }
    line_matches += match;
    number_line++;
  }
  flags_l_c(flags, line_matches, file_name, count_files);
}

void flags_l_c(use_flags *flags, int line_matches, char *file_name,
               int count_files) {
  if (flags->l && line_matches > 0) printf("%s\n", file_name);
  if (flags->c && !flags->l) {
    if (count_files > 1 && !flags->h) {
      printf("%s:%d\n", file_name, line_matches);
    } else {
      printf("%d\n", line_matches);
    }
  }
}

void flag_n(use_flags *flags, int count_files, char *file_name, int number_line,
            char *text) {
  if (!flags->l && !flags->c && !flags->o && flags->n) {
    if (count_files > 1 && !flags->h) {
      printf("%s:", file_name);
    }
    printf("%d:%s", number_line, text);
  }
}

void flag_v(use_flags *flags, int count_files, char *file_name, char *text) {
  if (!flags->l && !flags->c && !flags->n && !flags->o) {
    if (count_files > 1 && !flags->h && !flags->o) {
      printf("%s:", file_name);
    }
    printf("%s", text);
  }
}

void flag_o(use_flags *flags, int count_files, char *file_name, int number_line,
            regmatch_t *one_match, char *text) {
  if (flags->o && !flags->c) {
    if (count_files > 1 && !flags->h) {
      printf("%s:", file_name);
    }
    if (flags->n) {
      printf("%d:", number_line);
    }
    for (int i = one_match[0].rm_so; i < one_match[0].rm_eo; i++) {
      printf("%c", text[i]);
    }
    printf("\n");
  }
}