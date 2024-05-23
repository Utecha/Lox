CC = gcc
CFLAGS = -std=c99 -Wall -Wextra -Wno-unused-parameter
LINK = -pg

DBG = -O0 -DDEBUG -ggdb
DBGFLAGS := $(CFLAGS) $(DBG)

REL = -O3
RELFLAGS := $(CFLAGS) $(REL)

SRCDIR = src
BINDIR = bin

OBJDIR := $(SRCDIR)/obj
DBGDIR := $(BINDIR)/dbg
RELDIR := $(BINDIR)/rel

SRC := $(wildcard $(SRCDIR)/*.c)
OBJ := $(patsubst $(SRCDIR)/%.c, $(OBJDIR)/%.o, $(SRC))

INSTDIR = /usr/local/bin/

TARG = clox
DBGTARG := $(DBGDIR)/$(TARG)
RELTARG := $(RELDIR)/$(TARG)

all: release

release: $(RELTARG) | $(RELDIR)
	@ cp $(RELTARG) ./

debug: $(DBGTARG) | $(DBGDIR)

install: release
	@ printf "Copying %s to %s\n" $(TARG) $(INSTDIR); \
	sudo cp $(RELTARG) $(INSTDIR) && \
	printf "\033[1;32mInstall Successful - %s --> [%s/%s]\033[0m\n" $(RELTARG) $(INSTDIR) $(TARG)

uninstall: clean
	@ printf "\033[1;33mRemoving\033[0m %s from [%s]\n" $(TARG) $(INSTDIR); \
	sudo rm $(INSTDIR)/$(TARG) && \
	printf "\033[1;32mSuccessfully Uninstalled %s\033[0m\n" $(TARG)

clean:
	@ printf "Cleaning %s...\n" $(TARG); \
	rm -rf $(OBJDIR) $(BINDIR); \
	if [ -e $(TARG) ]; then \
		rm $(TARG); \
	fi; \
	printf "Cleaned %s successfully.\n" $(TARG)

$(DBGTARG): $(OBJ) | $(DBGDIR)
	$(CC) $(DBGFLAGS) $^ -o $@ $(LINK)

$(RELTARG): $(OBJ) | $(RELDIR)
	$(CC) $(RELFLAGS) $^ -o $@

$(OBJDIR)/%.o: $(SRCDIR)/%.c | $(OBJDIR)
	@ printf "%-8s: %-16s --> %s\n" "compiling" $< $@; \
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJDIR):
	@ mkdir -p $(OBJDIR)

$(DBGDIR):
	@ mkdir -p $(DBGDIR)

$(RELDIR):
	@ mkdir -p $(RELDIR)

$(BINDIR):
	@ mkdir -p $(BINDIR)

.PHONY: all release debug install uninstall clean
.DEFAULT: all
