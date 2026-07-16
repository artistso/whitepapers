LATEXMK ?= latexmk
TARGET := phase_space_clarification

.PHONY: all clean distclean

all: $(TARGET).pdf

$(TARGET).pdf: $(TARGET).tex references.bib $(wildcard sections/*.tex)
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error $(TARGET).tex

clean:
	$(LATEXMK) -c $(TARGET).tex

distclean:
	$(LATEXMK) -C $(TARGET).tex
