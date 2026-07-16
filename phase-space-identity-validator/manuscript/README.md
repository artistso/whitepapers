# Technical-note manuscript

This directory contains the reproducible LaTeX source for:

> **Mixed Derivatives in Phase Space: Poisson Geometry, Quantum Commutators, and Quantized Circulation**

The paper is an expository mathematical-physics clarification. It does not claim a new physical law. Its validator correspondence table maps the motivating ansatz to the stable diagnostics implemented by the software package.

## Structure

```text
manuscript/
├── phase_space_clarification.tex
├── references.bib
├── Makefile
└── sections/
    ├── 01_introduction.tex
    ├── 02_diagnosis.tex
    ├── 03_symplectic_poisson.tex
    ├── 04_quantum_noncommutativity.tex
    ├── 05_quantized_circulation.tex
    ├── 06_angular_momentum.tex
    ├── 07_diagnostic_dictionary.tex
    ├── 08_research_extensions.tex
    └── 09_conclusion.tex
```

## Local build

A TeX installation must provide `latexmk`, `biber`, `biblatex`, `lmodern`, and the standard LaTeX extra packages.

```bash
cd phase-space-identity-validator/manuscript
make
```

The output is:

```text
phase_space_clarification.pdf
```

Generated PDFs and LaTeX intermediates are ignored by Git. Use:

```bash
make clean
make distclean
```

`clean` removes intermediate files while retaining the PDF. `distclean` removes all generated outputs.

## Continuous integration

The repository workflow compiles the manuscript with `latexmk`, checks that the PDF is nonempty and readable with `pdfinfo`, and uploads the result as the `phase-space-clarification-pdf` workflow artifact.

The validated reference build is nine pages and compiles without unresolved references, LaTeX warnings, or overfull boxes.
