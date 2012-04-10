# What?

The goal of this Python module is to extract the main content of a webpage (like [Readability](http://www.readability.com/) for instance).

Ideally it would work on news websites & blogs, and it should work for a vast majority of languages.

# Reference

The main algorithm is from the paper [*CoreEx: Content Extraction from Online News Articles*](http://ilpubs.stanford.edu:8090/832/) by Jyotika Prasad & Andreas Paepcke.

You should note that this is an experiment so I may try different heuristics to improve the results (and so do not fully respect the algorithms described in the paper).

# Try it

Just drop some articles from your favorite news websites in a directory called tests, (your articles should have the `.in.html` extension) and run the script, you'll get the content of the articles in `*.out.html` files.

You can also simply call `summary` from a Python REPL with an URL if you wish...

