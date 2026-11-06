# UltraVision USA website

The marketing site for UltraVision Corporation (ultravisionusa.com): a fast, static,
multi-page site with no framework. Sources live in `src/`; `python tools/build.py`
assembles them into `dist/`, which is what gets deployed.

## What is here

| Path | Purpose |
| --- | --- |
| `src/pages/*.html` | One source file per page: a small front-matter block (title, description, path) followed by the page body. |
| `src/partials/` | Shared `head.html`, `nav.html` and `footer.html`. Change the menu or footer once here. |
| `src/redirects.txt` | Old WordPress URLs mapped to their new homes. Becomes redirect stub pages and `.htaccess` rules. |
| `assets/css/site.css` | The whole stylesheet. Design tokens (colours, radii, fonts) are CSS variables at the top. |
| `assets/js/site.js` | Menu, dropdowns, scroll reveal, contact form, external video base URL. Configuration constants are at the top. |
| `assets/img/` | WebP images sized for the web, plus the logo, favicons and the Open Graph image under `brand/`. |
| `assets/docs/` | PDFs linked from the site: FDA 510(k) letters, ISO 13485 certificate, user manual. The MC-mode explanation is deliberately not here; it is sent on request. |
| `tools/build.py` | Builds `dist/`: pages, `sitemap.xml`, redirect stubs, `.htaccess`, and copies assets. Standard library only. |
| `tools/check_links.py` | Verifies every internal link, image and anchor in `dist/`. |
| `.github/workflows/pages.yml` | Builds, link-checks and deploys `dist/` to GitHub Pages on every push to `master`. |
| `CNAME`, `robots.txt`, `site.webmanifest` | Domain binding for GitHub Pages, crawler rules, web app manifest. Copied into `dist/`. |
| `dist/` | **Generated, not committed.** Run the build to create it. |

Pages: home, products (overview, XS, XC, XR), AI marketplace, specialties, research,
MC-mode, OEM, education, about, contact, 404.

## Editing the site

1. Edit a page in `src/pages/` (or the menu and footer in `src/partials/`).
2. Build:

   ```bash
   python tools/build.py
   ```

3. Check links:

   ```bash
   python tools/check_links.py
   ```

4. Preview locally:

   ```bash
   python -m http.server 8765 --directory dist
   ```

   then open http://localhost:8765/.

Pages use `{{ROOT}}` for links and asset paths so the same files work at the domain
root and under a sub-path (for example `ucfchuck.github.io/ultravisionusa-website/`).
The redirect stubs and `404.html` use absolute paths and assume the domain root.

### Adding a page

Create `src/pages/my-page.html`:

```html
---
title: My page title
description: One or two sentences for search engines and link previews.
path: my-page/
---
<section class="section"><div class="container"> ... </div></section>
```

Build; it appears at `/my-page/` and in the sitemap. Add it to `src/partials/nav.html`
and `footer.html` if it belongs in the menus. Front-matter keys: `title`, `description`,
`path`, optional `priority` (sitemap), `image` (Open Graph image path), `extra_head`,
`out` (file name override), `absolute: true` (use `/` instead of relative links),
`sitemap: false`.

### Images

Drop web-ready images into `assets/img/<group>/`. Keep them around 1200 to 1400 px wide and
save as WebP (quality 80 to 85). Give every `<img>` an `alt`, `width` and `height`, and add
`loading="lazy"` for anything below the first screen.

### Contact form

The form posts to the endpoint in `CONTACT_ENDPOINT` at the top of `assets/js/site.js`.
It is empty by default, which makes the form open the visitor's email app with the message
filled in. To receive submissions without relying on the visitor's mail client, create a free
form endpoint (Formspree, Web3Forms, Basin or similar), paste its URL into `CONTACT_ENDPOINT`
and rebuild. Links such as `/contact/?interest=AI%20Marketplace` pre-select the interest.

### MSK scanning videos

The specialties page embeds the scanning videos from the WordPress uploads folder on the
current host (`MEDIA_BASE` in `assets/js/site.js`). They are 20 to 50 MB each, so they are
not stored in this repository. Before retiring WordPress, copy
`wp-content/uploads/2019/10` and `2019/11` somewhere permanent (a folder on the new host,
object storage or a CDN) and point `MEDIA_BASE` at it.

## Deploying

### Option A: GitHub Pages at ultravisionusa.com (recommended)

1. GitHub Pages serves private repositories only on paid plans. Either make this repository
   public (the site is public anyway) or keep it private on GitHub Pro/Team.
2. In the repository: Settings, Pages, Build and deployment, Source: **GitHub Actions**.
   The workflow in `.github/workflows/pages.yml` then runs on every push to `master`.
3. Settings, Pages, Custom domain: `ultravisionusa.com`, then tick **Enforce HTTPS** once
   the certificate is issued (a few minutes after DNS resolves).
4. DNS for ultravisionusa.com is served by SiteGround (ns1/ns2.siteground.net), the host of the
   old WordPress site, and email is on GoDaddy (secureserver.net MX records). In SiteGround
   Site Tools, Domain, DNS Zone Editor, change only the web records below and leave every MX
   and mail-related record alone or email will stop:

   | Type | Name | Value |
   | --- | --- | --- |
   | A | @ | 185.199.108.153 |
   | A | @ | 185.199.109.153 |
   | A | @ | 185.199.110.153 |
   | A | @ | 185.199.111.153 |
   | CNAME | www | ucfchuck.github.io |

   Remove the old A record that points at the WordPress host (34.174.219.61) and the old
   `www` alias. DNS changes can take up to a day to propagate everywhere. The WordPress site
   stays untouched on SiteGround and can be reached again at any time by pointing the records
   back, so keep that hosting plan running until the new site has been live for a while.

### Option B: upload to the current web host (GoDaddy, cPanel or any Apache host)

1. Run `python tools/build.py`.
2. Upload the **contents** of `dist/` into the web root (`public_html`), including the hidden
   `.htaccess`: it provides the HTTPS and `www` redirects, the 404 page and real 301
   redirects from the old WordPress URLs.
3. Remove or rename the WordPress `index.php` so `index.html` is served.

### Option C: Netlify, Vercel or Cloudflare Pages

Point the service at this repository with build command `python tools/build.py` and publish
directory `dist`. Add the custom domain in the service's dashboard and follow its DNS
instructions.

## Go-live checklist

- [ ] Confirm the Intelligence tier price on the AI Marketplace page (shown as planned pricing of $499 per month).
- [ ] Decide which beta and marketplace claims should be public before launch.
- [ ] Set `CONTACT_ENDPOINT` so form submissions arrive by email without relying on the visitor's mail client.
- [ ] Move the MSK videos off WordPress and update `MEDIA_BASE`.
- [ ] Verify reimbursement amounts on the Education page against the current fee schedule, or remove the amounts column.
- [ ] After DNS switches, submit `https://ultravisionusa.com/sitemap.xml` in Google Search Console.
- [ ] Keep the WordPress site reachable for a short time (or export it) in case any content or media is still needed.
- [ ] Once Google Patents lists US 12,773,182, link the patent number on the MC-mode page to it.
- [ ] Delete the MC-mode explanation PDF from the WordPress media library (`wp-content/uploads/2021/07/Explanation-of-MC-mode-basic-4-.pdf` and `.pptx`); it is still publicly downloadable there even though the new site only offers it on request.