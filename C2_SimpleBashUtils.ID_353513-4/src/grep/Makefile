#Compiler
CC = gcc

#Compiler flags
CFLAGS = -Wall -Wextra -Werror -std=c11

#Directories
SRC_DIR = .
COMMON_DIR = ../common

#Source files
SRCS = $(SRC_DIR)/s21_grep.c $(wildcard $(COMMON_DIR)/*.c)

# Header files (dependencies)
HEADERS = $(SRC_DIR)/s21_grep.h $(wildcard $(COMMON_DIR)/*.h)

# Executable file
EXEC = s21_grep

# All target
all: $(EXEC)

# Compile s21_grep
$(EXEC): $(SRCS) $(HEADERS)
	$(CC) $(CFLAGS) -o $@ $(SRCS)

# Clean target
clean:
	rm -f $(EXEC)

# PHONY targets
.PHONY: all clean
