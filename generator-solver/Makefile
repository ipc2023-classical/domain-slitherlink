
PROGS := generate solve

all: $(PROGS)

generate: generate.hs Slitherlink.hs
	ghc -O2 -Wall -threaded --make generate.hs

solve: solve.hs Slitherlink.hs
	ghc -O2 -Wall -threaded --make solve.hs

clean:
	rm -f *.hi
	rm -f *.o
	rm -f $(PROGS)
.PHONY: all clean
