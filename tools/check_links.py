#!/usr/bin/env python3
"""
Check every internal link, image, script, stylesheet and anchor in the built site.

  python tools/check_links.py

Exit status is 1 when something is broken. External links are listed but not fetched.
"""
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")
SKIP_DIRS = {".git", "node_modules"}


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []      # (attr, value, line)
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for attr in ("href", "src", "data-src", "srcset"):
            if attr in a and a[attr]:
                if attr == "srcset":
                    for part in a[attr].split(","):
                        self.refs.append((attr, part.strip().split(" ")[0], self.getpos()[0]))
                else:
                    self.refs.append((attr, a[attr], self.getpos()[0]))


def html_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.endswith(".html"):
                yield os.path.join(dirpath, f)


def main():
    if not os.path.isdir(ROOT):
        print("dist/ not found; run python tools/build.py first")
        return 1
    pages = {}
    for path in html_files():
        c = Collector()
        with open(path, encoding="utf-8") as fh:
            c.feed(fh.read())
        pages[path] = c

    problems = []
    external = set()
    for path, c in pages.items():
        base_dir = os.path.dirname(path)
        for attr, value, line in c.refs:
            if value.startswith(("http://", "https://")):
                if "localhost" in value or "ultravisionusa.com/wp-content" in value:
                    pass  # media hosted on the old site; resolved by MEDIA_BASE at runtime
                external.add(value)
                continue
            if value.startswith(("mailto:", "tel:", "javascript:", "data:")):
                continue
            if attr == "data-src":
                continue  # relative to MEDIA_BASE, not to the site
            parts = urlsplit(value)
            target_path = unquote(parts.path)
            fragment = parts.fragment
            if target_path == "":
                target_file = path
            else:
                if target_path.startswith("/"):
                    target = os.path.join(ROOT, target_path.lstrip("/"))
                else:
                    target = os.path.normpath(os.path.join(base_dir, target_path))
                if target_path.endswith("/") or os.path.isdir(target):
                    target_file = os.path.join(target, "index.html")
                else:
                    target_file = target
                if not os.path.exists(target_file):
                    problems.append("%s:%d  missing %s=\"%s\"" % (os.path.relpath(path, ROOT), line, attr, value))
                    continue
            if fragment and target_file.endswith(".html"):
                ids = pages.get(os.path.normpath(target_file))
                if ids is None:
                    with open(target_file, encoding="utf-8") as fh:
                        cc = Collector(); cc.feed(fh.read()); ids = cc
                    pages[os.path.normpath(target_file)] = ids
                if fragment not in ids.ids:
                    problems.append("%s:%d  missing anchor #%s in %s" % (os.path.relpath(path, ROOT), line, fragment, value))

    print("checked %d pages, %d internal references ok, %d external links" % (
        len(pages), sum(len(c.refs) for c in pages.values()) - len(problems), len(external)))
    for e in sorted(external):
        print("  external:", e)
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print("  " + p)
        return 1
    print("no broken internal links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
