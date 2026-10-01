/* ────────────────────────────────────────────────────────────────────────
   Site analytics — first-party.

   Events go to our own Cloudflare Worker and no further. No third party is
   involved, no cookie is set, nothing is kept in the browser, and no
   identifier follows anyone between visits: the Worker counts people by a
   hash that is re-salted every midnight and forgets the input immediately.
   That is why this needs no consent banner and why the privacy policy can
   still promise what it promises.

   This measures the website only. The ScreenToast app itself sends nothing —
   that promise is unchanged and should stay that way. (DMG downloads and
   update checks are counted by the Worker from the requests themselves;
   see worker/index.js.)

   What is reported:

     pageview                      one per page
     download… / checkout-click…   which button they used
     cta-…                         launch banner, launch film, feature request
     section-<id>                  how far down the page they actually got
     faq-<question>                which questions they had to open

   The last two explain the first. A page nobody scrolls and a page everybody
   scrolls past the price are the same zero sales.

   ENDPOINT is the single place this is configured. Until it is filled in,
   nothing is sent and no request is made, so the site behaves exactly as it
   does today.
   ──────────────────────────────────────────────────────────────────────── */
(function () {
  // Same origin, on a neutral path: the Worker serving this site writes the
  // event straight into the founder dashboard's dataset. A third-party host
  // (or a path called /collect) is on enough blocklists to undercount an
  // audience of Mac developers badly.
  var ENDPOINT = "/api/e";

  // Which product these events belong to, server-side.
  var SITE = "screentoast";

  if (ENDPOINT.indexOf("REPLACE_") === 0) return;

  // Respect an explicit do-not-track signal. Costs a few visits in the
  // numbers and keeps the site honest about what it said it would do.
  if (navigator.doNotTrack === "1" || window.doNotTrack === "1") return;

  /**
   * sendBeacon with a text/plain body is a "simple" request: the browser
   * fires no CORS preflight, and the send survives the page being closed —
   * which matters, because the most interesting click is the one that
   * navigates away.
   */
  function send(event) {
    var body = JSON.stringify({
      s: SITE,
      e: event,
      p: location.pathname,
      r: document.referrer || ""
    });
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon(ENDPOINT, new Blob([body], { type: "text/plain" }));
        return;
      }
    } catch (e) {}
    try {
      fetch(ENDPOINT, { method: "POST", body: body, keepalive: true, mode: "no-cors" });
    } catch (e) {}
  }

  /* ── Each event counts once per visit ───────────────────────────────────
     Section events multiply by however many sections a page has, and a
     reader scrolling up and down would count several times over. One per
     name per session keeps the numbers meaningful.

     sessionStorage throws in a private window or with site data blocked, so
     every access is guarded — a failure must not swallow the event. */
  var SEEN_KEY = "va-seen";
  var seen = null;

  function once(name) {
    if (seen === null) {
      try {
        seen = JSON.parse(sessionStorage.getItem(SEEN_KEY) || "{}");
      } catch (e) {
        seen = {};
      }
    }
    if (seen[name]) return false;
    seen[name] = 1;
    try {
      sessionStorage.setItem(SEEN_KEY, JSON.stringify(seen));
    } catch (e) {}
    return true;
  }

  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  send("pageview");

  onReady(function () {
    /* ── Clicks that were tagged in the markup ──────────────────────────── */
    document.addEventListener("click", function (e) {
      var host = e.target.closest ? e.target.closest("[data-event]") : null;
      if (!host) return;
      var name = host.getAttribute("data-event");
      if (name) send(name);
    });

    /* ── How far down the page people get ───────────────────────────────
       Every section already carries an id for its nav anchor, so this needs
       no markup at all: the ids are the report.

       The margin matters more than it looks. A threshold ratio can never be
       reached by a section taller than the viewport, so instead this fires
       when a section overlaps the middle half of the screen — which behaves
       the same whatever the section's height. */
    var sections = document.querySelectorAll("section[id]");
    if (sections.length && "IntersectionObserver" in window) {
      var observer = new IntersectionObserver(
        function (entries) {
          for (var i = 0; i < entries.length; i++) {
            var entry = entries[i];
            if (!entry.isIntersecting) continue;
            var name = "section-" + entry.target.id;
            if (once(name)) send(name);
            observer.unobserve(entry.target);
          }
        },
        { rootMargin: "-25% 0px -25% 0px", threshold: 0 }
      );
      for (var i = 0; i < sections.length; i++) observer.observe(sections[i]);
    }

    /* ── Which questions people had to open ─────────────────────────────
       An opened FAQ item is the page admitting it failed to answer
       something. The most-opened question is copy that belongs further up. */
    var items = document.querySelectorAll("details");
    for (var j = 0; j < items.length; j++) {
      (function (item) {
        item.addEventListener("toggle", function () {
          if (!item.open) return;
          var summary = item.querySelector("summary");
          var text = (summary ? summary.textContent : "").trim().toLowerCase();
          var slug = text
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "")
            .slice(0, 44);
          if (!slug) return;
          var name = "faq-" + slug;
          if (once(name)) send(name);
        });
      })(items[j]);
    }
  });
})();
