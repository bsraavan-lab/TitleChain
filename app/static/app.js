/* TitleChain — the small amount of behaviour that HTMX does not already give us.
   No framework, no CDN, no build step. Everything here is either a keyboard
   path, a clipboard write, or a class toggle.

   Design rule applied throughout: a control used many times a day gets NO
   animation, because motion makes a repeated action feel slow. The palette
   opens instantly; only the toast and the menus animate. */

(function () {
  'use strict';

  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ── toast ──────────────────────────────────────────────────────────────
     Used only to confirm something invisible happened (a clipboard write).
     Never for anything the user must not miss — an unread page is a row in the
     table, not a message that fades. */
  var toastEl = $('#toast'), toastT;
  function toast(msg) {
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add('on');
    clearTimeout(toastT);
    toastT = setTimeout(function () { toastEl.classList.remove('on'); }, 1900);
  }

  /* ── copy ───────────────────────────────────────────────────────────────
     One handler for every [data-copy] on the page, so the order block and the
     bar's copy of it can never drift apart. */
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-copy]');
    if (!btn) return;
    var text = btn.getAttribute('data-copy');
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(function () {
        toast('Request copied — paste it into TNREGINET');
      }, function () { fallbackCopy(text); });
    } else { fallbackCopy(text); }
  });

  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text; ta.setAttribute('readonly', '');
    ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); toast('Request copied'); }
    catch (err) { toast('Press ⌘C to copy'); }
    document.body.removeChild(ta);
  }

  /* ── dropzone ───────────────────────────────────────────────────────────
     The <label>/<input> pair already handles click and keyboard; this only adds
     drag and drop, and only where the markup asked for it. */
  var dz = $('[data-dropzone]');
  if (dz) {
    var input = dz.querySelector('input[type=file]');
    ['dragenter', 'dragover'].forEach(function (ev) {
      dz.addEventListener(ev, function (e) {
        e.preventDefault(); dz.classList.add('is-over');
      });
    });
    ['dragleave', 'drop'].forEach(function (ev) {
      dz.addEventListener(ev, function (e) {
        e.preventDefault(); dz.classList.remove('is-over');
      });
    });
    dz.addEventListener('drop', function (e) {
      if (!e.dataTransfer || !e.dataTransfer.files.length) return;
      input.files = e.dataTransfer.files;
      dz.submit();
    });
  }

  /* ── the rail follows the finding ───────────────────────────────────────
     Clicking any "Show me" marks its finding as the one currently pinned in the
     rail, so after three clicks she can still tell which row she is looking at.
     A "—" cell also pulls its own crop, so a value she is being asked to type
     is never typed from memory. */
  document.addEventListener('click', function (e) {
    var src = e.target.closest('[data-source]');
    if (src) {
      $$('.finding.is-open').forEach(function (n) { n.classList.remove('is-open'); });
      var owner = src.closest('.finding');
      if (owner) owner.classList.add('is-open');
    }
    var cell = e.target.closest('[data-evidence]');
    if (cell && window.htmx) {
      window.htmx.ajax('GET', '/evidence/' + cell.getAttribute('data-evidence'),
                       { target: '#rail', swap: 'innerHTML' });
    }
    /* Below 1080px the rail is not a rail — it sits under the findings. A
       "Show me" that changes something 2000px off-screen has done nothing, so
       on those widths we take her to it. */
    if ((src || cell) && window.innerWidth < 1080) {
      var rail = $('#rail');
      if (rail) setTimeout(function () {
        rail.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 60);
    }
  });

  /* ── the primary action follows her down the page ───────────────────────
     Revealed only once the card that explains it has scrolled away: the same
     button twice on one screen reads as two different buttons. */
  var order = $('#order'), barCta = $('.bar-cta');
  if (order && barCta && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      barCta.hidden = entries[0].isIntersecting;
    }, { rootMargin: '-60px 0px 0px 0px' }).observe(order);
  }

  /* ── keyboard ───────────────────────────────────────────────────────────
     Shortcuts are for the repeat user at month three, never the only path to
     anything: every one of these has a visible control as well. */
  function typing(el) {
    return el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' ||
                  el.isContentEditable);
  }

  function findings() { return $$('.finding[data-finding]'); }

  function move(dir) {
    var list = findings();
    if (!list.length) return;
    var i = list.indexOf(document.activeElement);
    var next = list[Math.max(0, Math.min(list.length - 1, i < 0 ? 0 : i + dir))];
    next.focus();
    next.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  document.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault(); openPalette(); return;
    }
    if (typing(document.activeElement) || e.metaKey || e.ctrlKey || e.altKey) return;

    switch (e.key) {
      case 'j': move(1); e.preventDefault(); break;
      case 'k': move(-1); e.preventDefault(); break;
      case 'Enter': {
        var f = document.activeElement;
        if (f && f.classList && f.classList.contains('finding')) {
          var b = f.querySelector('[data-source]');
          if (b) { b.click(); e.preventDefault(); }
        }
        break;
      }
      case '/': openPalette(); e.preventDefault(); break;
      default: {
        var hit = $('[data-shortcut="' + e.key + '"]');
        if (hit) { hit.click(); e.preventDefault(); }
      }
    }
  });

  /* ── command palette ────────────────────────────────────────────────────
     Recognition over recall: she picks a property by name rather than
     remembering where it was in a list. Also the whole keyboard navigation
     story in one component. */
  var dlg = $('#palette'), pinput = $('#palette-input'), plist = $('#palette-list');
  var items = [], filtered = [], cursor = 0, loaded = false;

  function openPalette() {
    if (!dlg || dlg.open) return;
    dlg.showModal();
    pinput.value = ''; cursor = 0;
    load().then(render);
    pinput.focus();
  }

  function load() {
    if (loaded) return Promise.resolve();
    return fetch('/palette.json').then(function (r) { return r.json(); })
      .then(function (data) {
        items = (data.cases || []).map(function (c) {
          return { label: c.label, sub: c.sub, kind: 'Case', href: '/case/' + c.id };
        }).concat(data.commands || []);
        loaded = true;
      }).catch(function () { items = data_fallback(); loaded = true; });
  }

  function data_fallback() { return [{ label: 'All cases', kind: 'Go', href: '/' }]; }

  function render() {
    var q = pinput.value.trim().toLowerCase();
    filtered = items.filter(function (it) {
      return !q || (it.label + ' ' + (it.sub || '')).toLowerCase().indexOf(q) > -1;
    });
    cursor = Math.min(cursor, Math.max(0, filtered.length - 1));
    plist.innerHTML = '';
    filtered.forEach(function (it, i) {
      var li = document.createElement('li');
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', i === cursor ? 'true' : 'false');
      var name = document.createElement('span');
      name.textContent = it.label;
      li.appendChild(name);
      if (it.sub) {
        var sub = document.createElement('span');
        sub.className = 'meta'; sub.textContent = it.sub;
        li.appendChild(sub);
      }
      var kind = document.createElement('span');
      kind.className = 'pk'; kind.textContent = it.kind;
      li.appendChild(kind);
      li.addEventListener('click', function () { go(it); });
      plist.appendChild(li);
    });
    if (!filtered.length) {
      var empty = document.createElement('li');
      empty.className = 'meta';
      empty.textContent = 'Nothing matches “' + pinput.value + '”.';
      plist.appendChild(empty);
    }
  }

  function go(it) { dlg.close(); if (it.href) window.location.href = it.href; }

  if (dlg) {
    pinput.addEventListener('input', function () { cursor = 0; render(); });
    pinput.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { cursor = Math.min(cursor + 1, filtered.length - 1); render(); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { cursor = Math.max(cursor - 1, 0); render(); e.preventDefault(); }
      else if (e.key === 'Enter') { if (filtered[cursor]) go(filtered[cursor]); e.preventDefault(); }
    });
    $$('[data-open-palette]').forEach(function (b) {
      b.addEventListener('click', openPalette);
    });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
  }
})();
