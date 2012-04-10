#!/usr/bin/env python3.1
#-*- coding: utf-8 -*-

import lxml.etree
import lxml.html
import re
import unicodedata

"""This module can be used in order to extract the main content from blog
posts/news using roughly the algorithm described in the paper "CoreEx:
Content Extraction from Online News Articles" by Jyotika Prasad & Andreas
Paepcke (available here: http://ilpubs.stanford.edu:8090/832/).

The only "public" function is summary.
"""

__all__ = ['summary']
__author__ = 'Alexis Daboville <alexis.daboville@gmail.com>'

threshold = .9
weight_ratio = .95
weight_text = .05

def preprocess(elt):
    """Drop all the tree where the root is one of the following:
    * <form>
    * <iframe>
    * <script>
    * <style>
    * <!-- comments -->

    This operate directly on elt (i.e. no return value).
    """
    forbidden = ['form', 'iframe', 'script', 'style', lxml.etree.Comment]
    lxml.etree.strip_elements(elt, with_tail=False, *forbidden)


def normalize(txt):
    """Remove all the unicode "marks", e.g.:
    >>> normalize('un éléphant ça trompe énormément!')
    'un elephant ca trompe enormement!'
    """
    nfkd = unicodedata.normalize('NFKD', txt)
    return ''.join(x for x in nfkd if unicodedata.category(x)[0] != 'M')


def countwords(txt):
    """Count the number of words in txt."""
    txt = normalize(txt)
    return len(re.findall(r'\w+', txt))


def create_subsets(elt):
    """Set the textCnt, linkCnt, setTextCnt, and setLinkCnt variables
    to the right value to elt and to all its subtree recursively.
    """
    if elt.tag == 'a':
        elt.textCnt = 1
        elt.linkCnt = 1

    else:
        elt.textCnt = countwords(elt.text or '')
        elt.linkCnt = 0
        elt.setTextCnt = elt.textCnt
        elt.setLinkCnt = 0

        elt.S = set()

        for child in elt:
            create_subsets(child)
            elt.textCnt += child.textCnt
            elt.linkCnt += child.linkCnt

            tailTextCnt = countwords(child.tail or '')
            elt.textCnt += tailTextCnt
            elt.setTextCnt += tailTextCnt

            try:
                childRatio = (child.textCnt - child.linkCnt) / child.textCnt

                if childRatio > threshold:
                    elt.S.add(child)
                    elt.setTextCnt += child.textCnt
                    elt.setLinkCnt += child.linkCnt

            except ZeroDivisionError:
                pass # TODO: check the paper


def scoreone(elt, page_text):
    """Score the node using the formula:
    score = weight_ratio * (setTextCnt - setLinkCnt) / setTextCnt
          + weight_text * setTextCnt / page_text
    """
    try:
        if 'S' in elt.__dict__:
            elt.score = (weight_ratio * (elt.setTextCnt
                - elt.setLinkCnt) / elt.setTextCnt + weight_text
                * elt.setTextCnt / page_text)
    except ZeroDivisionError:
        pass # no text? no score, fair enough?


def setscores(elt, page_text=None):
    """Set the score of all elements in the subtree using the scoreone
    function.

    page_text is equal to the number of words in the whole tree,
    you probably don't want to use it.
    """
    page_text = page_text or elt.textCnt

    for child in elt:
        setscores(child, page_text)

    scoreone(elt, page_text)


def summary(filename_or_url, parser=None, base_url=None):
    """Take the same arguments as lxml.html.parse.

    Return an lxml element which (hopefully) contains all the content.
    """
    document = lxml.html.parse(filename_or_url, parser, base_url)
    root = document.getroot()

    body = root.body

    # hackish & ugly, but needed to add data to each node...
    # https://mailman-mail5.webfaction.com/pipermail/lxml/2010-April/005368.html
    alive = set(body.iterdescendants()) | {body}

    preprocess(body)
    create_subsets(body)
    setscores(body)

    best = max(alive, key=lambda x: x.score if 'score' in x.__dict__ else 0)

    for e in best:
        if e not in best.S:
            e.drop_tree()

    return best


if __name__ == '__main__':
    import glob

    for filename in glob.glob('tests/*'):
        if filename.endswith('.in.html'):
            content = summary(filename)

            with open(filename.rstrip('.in.html') + '.out.html', 'wb') as f:
                content = lxml.etree.tostring(content, pretty_print=True,
                                              encoding='utf-8')
                f.write(content)

