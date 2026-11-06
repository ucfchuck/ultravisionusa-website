/* UltraVision Corporation - site script (no dependencies) */
(function () {
  'use strict';

  /* ---------- Configuration ----------
     CONTACT_ENDPOINT: paste a Formspree / Web3Forms / Basin endpoint here, for example
       'https://formspree.io/f/xxxxxxxx'
     Leave it empty and the form falls back to opening the visitor's mail client. */
  var CONTACT_ENDPOINT = '';
  var CONTACT_EMAIL = 'sales@ultravisionusa.com';
  var CONTACT_PHONE = '561 403 4884';

  /* MEDIA_BASE: where the MSK scanning videos are hosted. They currently live in the
     WordPress uploads folder; point this somewhere else (CDN, object storage) when
     WordPress is retired. */
  var MEDIA_BASE = 'https://ultravisionusa.com/wp-content/uploads/';

  var nav = document.querySelector('.nav');
  var toggle = document.querySelector('.nav__toggle');
  var menu = document.querySelector('.nav__menu');
  /* Must match the @media (max-width: 1040px) breakpoint in site.css */
  var compact = window.matchMedia('(max-width: 1040px)');
  function isCompact() { return compact.matches; }

  /* ---------- Sticky nav shading ---------- */
  function onScroll() {
    if (!nav) return;
    nav.classList.toggle('is-scrolled', window.scrollY > 24);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- Mobile menu ---------- */
  if (toggle && nav && menu) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      document.body.style.overflow = open ? 'hidden' : '';
    });
    // If the window grows past the breakpoint while the panel is open, close it and restore scrolling
    compact.addEventListener('change', function (e) {
      if (!e.matches && nav.classList.contains('is-open')) {
        nav.classList.remove('is-open');
        toggle.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
      }
    });
    menu.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        if (isCompact()) {
          nav.classList.remove('is-open');
          toggle.setAttribute('aria-expanded', 'false');
          document.body.style.overflow = '';
        }
      });
    });
  }

  /* ---------- Dropdowns (click/tap + keyboard; hover on desktop) ---------- */
  var dropdowns = document.querySelectorAll('.nav__menu .has-sub');
  function closeAll(except) {
    dropdowns.forEach(function (li) {
      if (li === except) return;
      li.querySelector('.nav__link').setAttribute('aria-expanded', 'false');
      li.querySelector('.sub').classList.remove('is-open');
    });
  }
  dropdowns.forEach(function (li) {
    var btn = li.querySelector('.nav__link');
    var sub = li.querySelector('.sub');
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var open = sub.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      closeAll(li);
    });
    li.addEventListener('mouseenter', function () {
      if (!isCompact()) { sub.classList.add('is-open'); btn.setAttribute('aria-expanded', 'true'); }
    });
    li.addEventListener('mouseleave', function () {
      if (!isCompact()) { sub.classList.remove('is-open'); btn.setAttribute('aria-expanded', 'false'); }
    });
    li.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { sub.classList.remove('is-open'); btn.setAttribute('aria-expanded', 'false'); btn.focus(); }
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.has-sub')) closeAll(null);
  });

  /* ---------- Mark the current page in the nav ---------- */
  var here = location.pathname.replace(/index\.html$/, '');
  document.querySelectorAll('.nav__menu a[href]').forEach(function (a) {
    var href = a.getAttribute('href');
    if (!href || href.charAt(0) === '#') return;
    var target = new URL(href, location.href).pathname.replace(/index\.html$/, '');
    if (target === here) {
      a.classList.add('is-active');
      var parent = a.closest('.has-sub');
      if (parent) parent.querySelector('.nav__link').classList.add('is-active');
    }
  });

  /* ---------- Reveal on scroll ---------- */
  var revealEls = document.querySelectorAll('.reveal');
  function revealAll() { revealEls.forEach(function (el) { el.classList.add('is-in'); }); }
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(function (el) { io.observe(el); });
    // Safety net: never leave content hidden if the observer is throttled (background tab, print, etc.)
    setTimeout(revealAll, 2500);
    window.addEventListener('beforeprint', revealAll);
  } else {
    revealAll();
  }

  /* ---------- Videos hosted outside the repository ---------- */
  document.querySelectorAll('video[data-src]').forEach(function (v) {
    var src = v.getAttribute('data-src');
    v.setAttribute('src', /^https?:/.test(src) ? src : MEDIA_BASE + src);
  });

  /* ---------- Contact form ---------- */
  var form = document.querySelector('form[data-contact]');
  if (form) {
    var status = form.querySelector('.form__status');
    var button = form.querySelector('button[type="submit"]');
    var interestField = form.querySelector('[name="interest"]');

    // Pre-select the interest from the URL, e.g. /contact/?interest=AI%20Marketplace
    var wanted = new URLSearchParams(location.search).get('interest');
    if (wanted && interestField) {
      Array.prototype.forEach.call(interestField.options, function (o) {
        if (o.value.toLowerCase() === wanted.toLowerCase()) interestField.value = o.value;
      });
    }

    var show = function (kind, text) {
      if (!status) return;
      status.className = 'form__status ' + (kind === 'ok' ? 'is-ok' : 'is-err');
      status.textContent = text;
      status.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var trap = form.querySelector('.hp input');
      if (trap && trap.value) return; // honeypot caught a bot
      var data = new FormData(form);
      var name = String(data.get('name') || '').trim();
      var email = String(data.get('email') || '').trim();
      var org = String(data.get('organization') || '').trim();
      var interest = String(data.get('interest') || '').trim();
      var message = String(data.get('message') || '').trim();
      if (!name || !email || !message) {
        show('err', 'Please fill in your name, email and a short message.');
        return;
      }
      if (!CONTACT_ENDPOINT) {
        var subject = 'Website inquiry' + (interest ? ': ' + interest : '');
        var body = 'Name: ' + name + '\nEmail: ' + email + '\nOrganization: ' + org + '\nInterest: ' + interest + '\n\n' + message;
        window.location.href = 'mailto:' + CONTACT_EMAIL + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
        show('ok', 'Your email app should open with the message ready to send. If it does not, email us at ' + CONTACT_EMAIL + ' or call ' + CONTACT_PHONE + '.');
        return;
      }
      button.disabled = true;
      button.textContent = 'Sending...';
      fetch(CONTACT_ENDPOINT, { method: 'POST', headers: { 'Accept': 'application/json' }, body: data })
        .then(function (r) { if (!r.ok) throw new Error('bad status'); })
        .then(function () { form.reset(); show('ok', 'Thanks. Your message has been sent and we will be in touch shortly.'); })
        .catch(function () { show('err', 'Sorry, the message could not be sent. Please email ' + CONTACT_EMAIL + ' or call ' + CONTACT_PHONE + '.'); })
        .then(function () { button.disabled = false; button.textContent = 'Send message'; });
    });
  }

  /* ---------- Footer year ---------- */
  document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = String(new Date().getFullYear()); });
})();
