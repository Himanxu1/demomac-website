/* ────────────────────────────────────────────────────────────────────────
   Download gate — ask for an email before the DMG downloads.

   Every link to a .dmg on the site goes through here: the first click opens
   a dialog, the address goes to POST /api/download (worker/index.js, D1
   table `downloaders`), and the download then starts on its own. The address
   is remembered in this browser, so a second download is not asked again.

   No markup is needed on the buttons — any <a href="….dmg"> is caught, so a
   new page or a new release link is covered automatically. The analytics
   click beacon (analytics.js) still fires on the original click.

   A checkbox lets people skip the email and download anyway; that is counted
   (event `skip-email`) but nothing about them is stored.

   If our server cannot be reached, the download goes ahead anyway: losing an
   address is better than losing the person.
   ──────────────────────────────────────────────────────────────────────── */
(function () {
  var KEY = "st-download-email";
  var ENDPOINT = "/api/download";

  function remembered() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function remember(email) {
    try { localStorage.setItem(KEY, email); } catch (e) {}
  }

  function startDownload(href) {
    var a = document.createElement("a");
    a.href = href;
    a.setAttribute("download", "");
    a.style.display = "none";
    a.setAttribute("data-gate-pass", "");
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  var CSS = "" +
    ".dg{border:1px solid #26262e;border-radius:16px;padding:0;background:#121216;color:#b5b0a8;" +
    "width:min(440px,calc(100vw - 32px));font:16px/1.6 'IBM Plex Sans',-apple-system,sans-serif;" +
    "box-shadow:0 30px 80px rgba(0,0,0,.6)}" +
    ".dg::backdrop{background:rgba(8,8,10,.72);backdrop-filter:blur(6px)}" +
    ".dg form{padding:28px 26px 24px;margin:0;position:relative}" +
    ".dg h2{margin:0 0 6px;color:#f2efe9;font:800 22px/1.2 'Archivo',Helvetica,Arial,sans-serif;letter-spacing:-.01em}" +
    ".dg p{margin:0 0 18px;font-size:14.5px}" +
    ".dg label{display:block;font-size:13px;color:#8e8a84;margin-bottom:6px}" +
    ".dg input[type=email]{width:100%;box-sizing:border-box;padding:12px 14px;border-radius:10px;" +
    "border:1px solid #35353f;background:#08080a;color:#f2efe9;font:inherit;outline:none}" +
    ".dg input[type=email]:focus{border-color:#ff5b04;box-shadow:0 0 0 3px rgba(255,91,4,.18)}" +
    ".dg .dg-go{margin-top:14px;width:100%;padding:12px 20px;border:0;border-radius:10px;cursor:pointer;" +
    "background:#ff5b04;color:#160700;font:600 15px 'IBM Plex Sans',-apple-system,sans-serif}" +
    ".dg .dg-go:hover{background:#ff6f22}.dg .dg-go:disabled{opacity:.6;cursor:default}" +
    ".dg .dg-x{position:absolute;top:12px;right:12px;width:32px;height:32px;border:0;border-radius:8px;" +
    "background:transparent;color:#8e8a84;font-size:20px;line-height:1;cursor:pointer}" +
    ".dg .dg-x:hover{color:#f2efe9;background:#1a1a20}" +
    ".dg .dg-msg{min-height:1.4em;margin:10px 0 0;font-size:13.5px;color:#ff7a2f}" +
    ".dg .dg-fine{margin:12px 0 0;font-size:12.5px;color:#8e8a84}" +
    ".dg .dg-fine a{color:#b5b0a8}" +
    ".dg .dg-hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}" +
    ".dg .dg-skip{display:flex;align-items:center;gap:9px;margin:12px 0 0;font-size:13.5px;color:#b5b0a8;cursor:pointer}" +
    ".dg .dg-skip input{width:16px;height:16px;margin:0;accent-color:#ff5b04;cursor:pointer}" +
    ".dg input[type=email]:disabled{opacity:.45}";

  var dialog = null, pending = null;

  function build() {
    var style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);

    dialog = document.createElement("dialog");
    dialog.className = "dg";
    dialog.setAttribute("aria-labelledby", "dg-title");
    dialog.innerHTML =
      '<form novalidate>' +
        '<button type="button" class="dg-x" aria-label="Close">&times;</button>' +
        '<h2 id="dg-title">One step before your download</h2>' +
        '<p>Leave your email to hear about ScreenToast updates: new versions, fixes and ' +
          'features as they ship. Your download starts the moment you submit.</p>' +
        '<label for="dg-email">Your email</label>' +
        '<input id="dg-email" name="email" type="email" maxlength="200" required ' +
          'placeholder="you@company.com" autocomplete="email" inputmode="email">' +
        '<label class="dg-skip"><input type="checkbox" name="skip"> I don\u2019t need updates \u2014 just download</label>' +
        '<label class="dg-hp" aria-hidden="true">Website <input name="website" tabindex="-1" autocomplete="off"></label>' +
        '<button type="submit" class="dg-go">Download for Mac</button>' +
        '<p class="dg-msg" role="status" aria-live="polite"></p>' +
        '<p class="dg-fine">Only ScreenToast updates. No spam, and never shared or sold. ' +
          '<a href="/privacy">Privacy</a></p>' +
      '</form>';
    document.body.appendChild(dialog);

    var form = dialog.querySelector("form");
    var input = form.elements.email;
    var go = form.querySelector(".dg-go");
    var msg = form.querySelector(".dg-msg");
    var skip = form.elements.skip;

    skip.addEventListener("change", function () {
      input.disabled = skip.checked;
      msg.textContent = "";
      if (!skip.checked) input.focus();
    });

    dialog.querySelector(".dg-x").addEventListener("click", function () { dialog.close(); });
    // A click on the backdrop lands on the <dialog> itself.
    dialog.addEventListener("click", function (e) { if (e.target === dialog) dialog.close(); });
    dialog.addEventListener("close", function () {
      pending = null; msg.textContent = ""; skip.checked = false; input.disabled = false;
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var job = pending;
      if (!job) return;

      // Skipped: count it (no email, nothing stored) and download straight away.
      // Not remembered, so the next download asks again.
      if (skip.checked) {
        try {
          var body = JSON.stringify({ skip: true, source: job.source, page: location.pathname });
          if (navigator.sendBeacon) navigator.sendBeacon(ENDPOINT, new Blob([body], { type: "application/json" }));
          else fetch(ENDPOINT, { method: "POST", headers: { "content-type": "application/json" }, body: body, keepalive: true });
        } catch (err) {}
        dialog.close();
        startDownload(job.href);
        return;
      }

      var email = input.value.trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
        msg.textContent = "Enter a valid email address.";
        input.focus();
        return;
      }
      go.disabled = true;
      msg.textContent = "";

      fetch(ENDPOINT, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          email: email,
          source: job.source,
          page: location.pathname,
          website: form.elements.website.value
        })
      }).then(function (res) {
        if (res.ok || res.status >= 500) return { ok: true };
        return res.json().catch(function () { return {}; }).then(function (d) {
          return { ok: false, error: d.error || "Something went wrong. Try again." };
        });
      }, function () {
        return { ok: true };  // offline or blocked — download anyway
      }).then(function (r) {
        go.disabled = false;
        if (!r.ok) { msg.textContent = r.error; return; }
        remember(email);
        dialog.close();
        startDownload(job.href);
      });
    });
  }

  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button !== 0) return;
    var link = e.target.closest ? e.target.closest('a[href$=".dmg"]') : null;
    if (!link || link.hasAttribute("data-gate-pass")) return;
    if (remembered()) return;  // already asked in this browser
    if (typeof HTMLDialogElement !== "function") return;  // very old browser: just download

    // Not stopPropagation: analytics.js still counts which button was clicked.
    e.preventDefault();
    if (!dialog) build();
    pending = { href: link.href, source: link.getAttribute("data-event") || "" };
    if (!dialog.open) dialog.showModal();
    dialog.querySelector("input[type=email]").focus();
  });
})();
