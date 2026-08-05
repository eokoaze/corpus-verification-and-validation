all: paper

corpora:
	python3 fetch_corpora.py

results:
	python3 experiment.py duplicate truncate boilerplate
	python3 experiment.py foreign encoding
	python3 doclevel.py

figures:
	python3 figures.py

paper:
	pdflatex -interaction=nonstopmode main.tex
	bibtex main
	pdflatex -interaction=nonstopmode main.tex
	pdflatex -interaction=nonstopmode main.tex

clean:
	rm -f *.aux *.log *.bbl *.blg *.out
