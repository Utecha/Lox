JC = javac
NATIVE = native-image

SRCDIR = src/lox
TOOLDIR = src/tool

CLASSDIR = classes

TARG = jlox
RELTARG := $(CLASSDIR)/$(TARG)

all: release

release: build $(RELTARG)

build:
	$(JC) -d $(CLASSDIR) $(SRCDIR)/*.java

clean:
	@ printf "Cleaning %s...\n" $(TARG); \
	rm -rf $(CLASSDIR); \
	if [ -e $(TARG) ]; then \
		rm $(TARG); \
	fi; \
	printf "Cleaned %s successfully.\n" $(TARG)

$(RELTARG): $(CLASSDIR)
	$(NATIVE) -march=native --gc=G1 -O3 -Ob -cp $(CLASSDIR) lox.Lox -o $(TARG)

$(CLASSDIR):
	@ mkdir -p $(CLASSDIR)

.PHONY: all
.DEFAULT: all
