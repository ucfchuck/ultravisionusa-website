#!/usr/bin/env python3
"""
Assemble the static site into dist/.

  src/partials/head.html, nav.html, footer.html   shared chrome
  src/pages/*.html                                 one file per page: front matter + body
  src/redirects.txt                                old WordPress URLs -> new locations
  assets/, robots.txt, site.webmanifest, CNAME     copied as-is

Output (dist/ is created from scratch on every run):
  dist/index.html, dist/products/index.html, ...   the pages
  dist/<old-slug>/index.html                       redirect stubs for the old URLs
  dist/.htaccess                                   HTTPS/www/301 rules for Apache hosts
  dist/sitemap.xml

Run from anywhere:  python tools/build.py
No dependencies beyond the Python standard library.
"""
import datetime
import hashlib
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
PAGES = os.path.join(SRC, "pages")
PARTIALS = os.path.join(SRC, "partials")
DIST = os.path.join(ROOT, "dist")
SITE_URL = "https://ultravisionusa.com/"
SITE_NAME = "UltraVision Corporation"
COPY_DIRS = ["assets"]
COPY_FILES = ["robots.txt", "site.webmanifest", "CNAME"]


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def parse(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", text, re.S)
    if not m:
        raise SystemExit("page is missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def render(template, variables):
    def sub(match):
        key = match.group(1)
        if key not in variables:
            raise SystemExit("unknown placeholder {{%s}}" % key)
        return variables[key]
    return re.sub(r"\{\{([A-Z_]+)\}\}", sub, template)


def asset_version():
    """Short hash of the stylesheet and script, appended as ?v= so browsers fetch new versions."""
    h = hashlib.sha1()
    for rel in ("assets/css/site.css", "assets/js/site.js"):
        with open(os.path.join(ROOT, rel), "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:8]


def build_pages():
    head = read(os.path.join(PARTIALS, "head.html"))
    nav = read(os.path.join(PARTIALS, "nav.html"))
    footer = read(os.path.join(PARTIALS, "footer.html"))
    layout = head + nav + '<main id="main">\n' + "{{BODY}}" + "\n</main>\n" + footer
    version = asset_version()

    urls = []
    for name in sorted(os.listdir(PAGES)):
        if not name.endswith(".html"):
            continue
        meta, body = parse(read(os.path.join(PAGES, name)))
        path = meta.get("path", "")                      # "" | "products/" | "products/ultravision-xs/"
        out = meta.get("out") or (path + "index.html")
        depth = path.count("/")
        root = "/" if meta.get("absolute") == "true" else "../" * depth
        title = meta["title"]
        full_title = title if meta.get("home") == "true" else "%s | %s" % (title, SITE_NAME)
        variables = {
            "ROOT": root,
            "TITLE": full_title,
            "DESC": meta["description"],
            "URL": SITE_URL + path,
            "OG_IMAGE": SITE_URL + meta.get("image", "assets/img/brand/og-image.jpg"),
            "EXTRA_HEAD": meta.get("extra_head", ""),
            "BODY_CLASS": meta.get("body_class", ""),
            "ASSET_V": version,
            "BODY": body.strip(),
        }
        html = render(layout, variables)
        html = render(html, variables)   # second pass resolves placeholders inside the body
        write(os.path.join(DIST, out.replace("/", os.sep)), html)
        if meta.get("sitemap") != "false":
            urls.append((SITE_URL + path, meta.get("priority", "0.7")))
        print("wrote", out)
    return urls


def build_redirects():
    redirects = []
    redirects_file = os.path.join(SRC, "redirects.txt")
    if os.path.exists(redirects_file):
        for line in read(redirects_file).splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            old, new = line.split()
            redirects.append((old.strip("/"), new))
    stub = ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<title>Redirecting</title><meta name="robots" content="noindex">'
            '<link rel="canonical" href="{abs}">'
            '<meta http-equiv="refresh" content="0; url={new}">'
            '<script>location.replace("{new}");</script></head>'
            '<body><p>This page has moved to <a href="{new}">{abs}</a>.</p></body></html>\n')
    for old, new in redirects:
        write(os.path.join(DIST, old, "index.html"), stub.format(new=new, abs=SITE_URL + new.lstrip("/")))
    htaccess = ["# Generated by tools/build.py - Apache hosts only (ignored on GitHub Pages)",
                "ErrorDocument 404 /404.html",
                "AddType image/webp .webp",
                "AddType application/manifest+json .webmanifest",
                "<IfModule mod_expires.c>",
                "  ExpiresActive On",
                "  ExpiresByType image/webp \"access plus 30 days\"",
                "  ExpiresByType image/png \"access plus 30 days\"",
                "  ExpiresByType text/css \"access plus 7 days\"",
                "  ExpiresByType application/javascript \"access plus 7 days\"",
                "</IfModule>",
                "<IfModule mod_rewrite.c>",
                "  RewriteEngine On",
                "  RewriteCond %{HTTPS} off",
                "  RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]",
                "  RewriteCond %{HTTP_HOST} ^www\\.(.+)$ [NC]",
                "  RewriteRule ^ https://%1%{REQUEST_URI} [L,R=301]",
                "</IfModule>"]
    for old, new in redirects:
        # anchored so "/hip" never swallows "/hip-something"; fragments are dropped (Apache cannot send them)
        htaccess.append("RedirectMatch 301 ^/%s/?$ %s" % (re.escape(old), new.split("#")[0]))
    write(os.path.join(DIST, ".htaccess"), "\n".join(htaccess) + "\n")
    print("wrote %d redirect stubs and .htaccess" % len(redirects))


def build_sitemap(urls):
    today = datetime.date.today().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, priority in urls:
        lines.append("  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>" % (url, today, priority))
    lines.append("</urlset>\n")
    write(os.path.join(DIST, "sitemap.xml"), "\n".join(lines))
    print("wrote sitemap.xml (%d urls)" % len(urls))


def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    for d in COPY_DIRS:
        shutil.copytree(os.path.join(ROOT, d), os.path.join(DIST, d))
    for f in COPY_FILES:
        if os.path.exists(os.path.join(ROOT, f)):
            shutil.copy2(os.path.join(ROOT, f), os.path.join(DIST, f))
    urls = build_pages()
    build_redirects()
    build_sitemap(urls)
    print("done: dist/ is ready to deploy")


if __name__ == "__main__":
    sys.exit(main())
