// The camera that follows the scroll. Every word is in the HTML: without this script, or under
// reduced motion, the page stands still. A classic script in the head, because file:// refuses
// modules and the pinned layout has to be there before the first paint.
(function () {
  var root = document.documentElement;
  if (!window.matchMedia || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  root.classList.add("vivant");

  // Each of these gets --p, from 0 when its top enters the window to 1 when it reaches FIN.
  var ARRIVEES = ".carte, .preuves > div, .parole, .post, .clients, .valeurs > div, .frise li, .quadrant-bloc, " +
    ".double figure, .expert, .boite, .colonnes > div, .article > *, .appel, .reponse, .livre";
  var FIN = 0.55;      // of the window's height, from its top
  var PORTEE = 1 / 5;  // a stop pulls the page from a fifth of a screen away, Simon's pick on ficelle-site r67
  var large = matchMedia("(min-width: 62.01rem)");

  var scenes = [], lignes, mots = [], parole, lu;

  function haut(el) {
    var y = 0;
    for (; el; el = el.offsetParent) y += el.offsetTop;  // offsetTop ignores transforms: nothing measures its own motion
    return y;
  }
  function borne(n) { return n < 0 ? 0 : n > 1 ? 1 : n; }

  function mesure() {
    var bandeau = document.querySelector(".alerte"), entete = document.querySelector(".haut");
    if (bandeau && entete) {
      root.style.setProperty("--alerte", bandeau.offsetHeight + "px");
      root.style.setProperty("--haut", bandeau.offsetHeight + entete.offsetHeight + "px");
    }
    var vh = innerHeight, max = root.scrollHeight - vh;
    scenes.forEach(function (s) {
      var top = haut(s.el), h = s.el.offsetHeight;
      if (s.sorte === "pose") {           // the home's hero: pinned, the course is what the pin leaves
        var cadre = s.el.firstElementChild.offsetHeight;
        s.debut = 0;
        s.fin = h - cadre > 10 ? h - cadre : h;
      } else if (s.sorte === "traverse") { // a picture that drifts for as long as it is on screen
        s.debut = top - vh;
        s.fin = top + h;
      } else {
        s.debut = top - vh;
        s.fin = Math.min(top - vh * FIN, max);
        s.acquis = top < vh * 0.85 || s.fin <= s.debut;  // in the first screen, or nowhere to arrive from
      }
      s.vu = -1;
    });
    lignes = max;
    dessine();
  }

  function dessine() {
    var y = scrollY;
    scenes.forEach(function (s) {
      var p = s.acquis ? 1 : borne((y - s.debut) / (s.fin - s.debut));
      p = Math.round(p * 1000) / 1000;
      if (p !== s.vu) { s.vu = p; s.el.style.setProperty("--p", p); }
    });
    if (lu) lu.style.transform = "scaleX(" + (lignes > 0 ? borne(y / lignes) : 0) + ")";
    if (parole) {
      var allume = parole.vu * (mots.length + 1);
      mots.forEach(function (m, i) { m.classList.toggle("allume", i < allume); });
    }
  }

  // The stops are hooks set by hand in the pages, as on ficelle-site: data-stop is "start", "center"
  // or "end". Once the scroll rests the page glides to a near one. Big windows only: on a phone the
  // blocks are longer than the screen and a finger knows where it goes.
  function arrets() {
    var vh = innerHeight, max = root.scrollHeight - vh, sortie = [], garde = 0;
    document.querySelectorAll("[data-stop]").forEach(function (el) {
      var top = haut(el), h = el.offsetHeight, marge = parseFloat(getComputedStyle(el).scrollMarginTop) || 0;
      var sorte = el.dataset.stop, y;
      if (sorte === "center" && h > vh - marge) sorte = "start";
      if (sorte === "start") y = top - marge;
      else if (sorte === "end") y = top + h - vh;
      else y = top + h / 2 - (vh + marge) / 2;
      sortie.push(Math.round(Math.min(max, Math.max(0, y))));
    });
    // Two stops closer than a fifth of a screen would fight over the page: the first one holds.
    return sortie.sort(function (a, b) { return a - b; }).filter(function (y, i) {
      if (i && y - garde < vh * PORTEE) return false;
      garde = y;
      return true;
    }).filter(function (y) { return max - y >= vh * PORTEE; }).concat(max);  // the page's end is always a stop: the footer stays reachable
  }
  window.inviolia = { arrets: arrets };
  var tenu = false, glisse = false, minuteur;
  function glide(vers) {
    var de = scrollY, d = vers - de, ms = Math.min(520, 220 + Math.abs(d) * 1.4), t0 = performance.now();
    glisse = true;
    (function pas(t) {
      if (!glisse) return;
      var k = borne((t - t0) / ms);
      scrollTo(0, de + d * (1 - Math.pow(1 - k, 3)));
      if (k < 1) requestAnimationFrame(pas); else glisse = false;
    })(t0);
  }
  function repos() {
    if (tenu || glisse || !large.matches) return;
    var y = scrollY, proche = arrets().reduce(function (b, s) {
      return Math.abs(s - y) < Math.abs(b - y) ? s : b;
    }, Infinity);
    if (Math.abs(proche - y) > 1 && Math.abs(proche - y) < innerHeight * PORTEE) glide(proche);
  }
  function plusTard() { clearTimeout(minuteur); minuteur = setTimeout(repos, 140); }
  function coupe() {
    if (!glisse) return;
    glisse = false;
    var y = scrollY;
    setTimeout(function () { if (scrollY === y) plusTard(); }, 200);
  }

  // The live map. No new word: the counter's digits change, the feed's lines pair the HTML's own targets
  // and attacks, and the comets are paint. Nothing runs while it is off screen.
  function enVue(el, rappel) {
    if (!window.IntersectionObserver) { rappel(true); return; }
    new IntersectionObserver(function (e) { rappel(e[e.length - 1].isIntersecting); }).observe(el);
  }

  function compteur() {
    var el = document.querySelector(".chiffres .rouge");
    if (!el) return;
    var n = parseInt(el.textContent.replace(/\D/g, ""), 10), parSeconde = n / 86400;  // what "aujourd'hui" says
    var avant = performance.now(), vu = false;
    enVue(el, function (oui) { vu = oui; });
    setInterval(function () {
      if (!vu || document.hidden) return;
      var t = performance.now();  // off screen the attacks went on: it catches up on return
      n += Math.round((t - avant) / 1000 * parSeconde * (0.4 + Math.random() * 1.2));
      avant = t;
      el.textContent = String(n).replace(/\B(?=(\d{3})+$)/g, " ");
    }, 120);
  }

  // The DOM's order never changes, only CSS order does. The line that leaves comes back at the bottom as
  // a new one: later than the last, a target and an attack the page already has, a pair not on screen (Simon, r90).
  function flux() {
    var boite = document.querySelector(".flux");
    if (!boite || !boite.animate) return;
    var tour = [].slice.call(boite.children), vu = false;
    if (tour.length < 2) return;
    enVue(boite, function (oui) { vu = oui; });
    var cibles = [], sortes = [], heure = 0;
    tour.forEach(function (p) {
      var m = /^(\d+):(\d+):(\d+) · Inconnu → (.+?) · (.+?) *$/.exec(p.firstChild.textContent);
      heure = m[1] * 3600 + m[2] * 60 + +m[3];
      if (cibles.indexOf(m[4]) < 0) cibles.push(m[4]);
      if (sortes.indexOf(m[5]) < 0) sortes.push(m[5]);
    });
    function deux(n) { return (n < 10 ? "0" : "") + n; }
    function nouvelle(p) {
      var vues = tour.map(function (q) { return q.firstChild.textContent.slice(11); }), mots;
      do {
        mots = "Inconnu → " + cibles[Math.floor(Math.random() * cibles.length)] + " · " + sortes[Math.floor(Math.random() * sortes.length)] + " ";
      } while (vues.indexOf(mots) >= 0);
      heure += 1 + Math.floor(Math.random() * 2);       // about the 1.6 s a line takes on screen
      p.firstChild.textContent = deux(Math.floor(heure / 3600) % 24) + ":" + deux(Math.floor(heure / 60) % 60) + ":" + deux(heure % 60) + " · " + mots;
    }
    // A pair may wrap where another does not: each row holds the tallest, so the feed never changes height.
    function hauteur() {
      var p = tour[0], ecrit = p.firstChild.textContent, haut = 0;
      p.style.minHeight = "";
      cibles.forEach(function (c) {
        sortes.forEach(function (s) {
          p.firstChild.textContent = "00:00:00 · Inconnu → " + c + " · " + s + " ";
          haut = Math.max(haut, p.offsetHeight);
        });
      });
      p.firstChild.textContent = ecrit;
      tour.forEach(function (q) { q.style.minHeight = haut + "px"; });
    }
    hauteur();
    addEventListener("resize", hauteur);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(hauteur);
    function range() { tour.forEach(function (p, i) { p.style.order = i; }); }
    setInterval(function () {
      if (!vu || document.hidden) return;
      var sort = tour[0], pas = tour[1].offsetTop - sort.offsetTop;
      sort.animate({ clipPath: ["inset(0)", "inset(0 0 100% 0)"] }, { duration: 160, easing: "ease-in" }).onfinish = function () {
        nouvelle(sort);
        tour.push(tour.shift());
        range();
        tour.forEach(function (p) {
          p.animate({ translate: ["0 " + pas + "px", "0 0"] }, { duration: 420, easing: "cubic-bezier(.2, .7, .2, 1)" });
        });
      };
    }, 1600);
  }

  // Where the painted globe has land, in its 800 px square, of which the 500 / 420 frame keeps y 64 to 736.
  var TERRES = [[320, 230], [190, 340], [250, 390], [330, 500], [490, 510], [590, 190], [540, 340], [430, 680], [640, 320], [700, 250], [120, 300]];
  function carte() {
    var image = document.querySelector(".carte img");
    if (!image) return;
    var toile = document.createElement("canvas"), c = toile.getContext("2d");
    if (!c) return;
    toile.className = "tirs";
    toile.setAttribute("aria-hidden", "true");
    image.parentNode.insertBefore(toile, image.nextSibling);
    var tirs = [], vu = false, encours = false;

    function lieu() {
      var t = TERRES[Math.floor(Math.random() * TERRES.length)];
      return { x: t[0] / 800, y: (t[1] - 64) / 672 };
    }
    function tir(t) {
      var a = lieu(), b = lieu();
      while (Math.hypot(b.x - a.x, b.y - a.y) < 0.35) b = lieu();  // a long arc reads, a short one is a smudge
      return { a: a, b: b, h: { x: (a.x + b.x) / 2, y: Math.min(a.y, b.y) - 0.22 }, t0: t + Math.random() * 1400, ms: 900 + Math.random() * 700 };
    }
    function point(s, k, l, h) {
      var u = 1 - k;
      return [(u * u * s.a.x + 2 * u * k * s.h.x + k * k * s.b.x) * l, (u * u * s.a.y + 2 * u * k * s.h.y + k * k * s.b.y) * h];
    }
    function peint(t) {
      if (!vu || document.hidden) { encours = false; return; }
      requestAnimationFrame(peint);
      var dpr = Math.min(devicePixelRatio || 1, 2), l = Math.round(toile.clientWidth * dpr), h = Math.round(toile.clientHeight * dpr);
      if (!l || !h) return;
      if (toile.width !== l || toile.height !== h) { toile.width = l; toile.height = h; }
      c.clearRect(0, 0, l, h);
      c.lineCap = "round";
      var e = l / 500;
      tirs.forEach(function (s, i) {
        var k = (t - s.t0) / s.ms;
        if (k < 0) return;
        c.globalCompositeOperation = "lighter";    // a short bolt with its glow, nothing left behind it
        if (k < 1) {
          [[9, 0.16], [5, 0.3], [2, 1]].forEach(function (g) {
            c.lineWidth = g[0] * e;
            for (var n = 0; n < 14; n++) {
              var d = k - (n + 1) * 0.022, f = k - n * 0.022;
              if (d < 0) break;
              var p = point(s, d, l, h), q = point(s, f, l, h);
              c.strokeStyle = "rgba(255, 60, 90, " + g[1] * (1 - n / 14) + ")";
              c.beginPath(); c.moveTo(p[0], p[1]); c.lineTo(q[0], q[1]); c.stroke();
            }
          });
        } else {                           // blocked, every time
          var r = (k - 1) / 0.4, o = point(s, 1, l, h);
          [[6, 0.25], [2, 1]].forEach(function (g) {
            c.strokeStyle = "rgba(57, 229, 140, " + g[1] * Math.max(0, 1 - r) + ")";
            c.lineWidth = g[0] * e;
            c.beginPath(); c.arc(o[0], o[1], (2 + r * 11) * e, 0, 6.3); c.stroke();
          });
        }
        c.globalCompositeOperation = "source-over";
        if (k > 1.4) tirs[i] = tir(t);
      });
    }
    enVue(toile, function (oui) {
      vu = oui;
      if (!oui || encours) return;
      encours = true;
      var t = performance.now();
      while (tirs.length < 7) tirs.push(tir(t));
      tirs = tirs.map(function (s) { return t - s.t0 > s.ms * 1.4 ? tir(t) : s; });
      requestAnimationFrame(peint);
    });
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden && vu && !encours) { encours = true; requestAnimationFrame(peint); }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    compteur();
    flux();
    carte();
    var pose = document.querySelector(".scene-hero");
    if (pose) scenes.push({ el: pose, sorte: "pose" });
    document.querySelectorAll(".bandeau").forEach(function (el) { scenes.push({ el: el, sorte: "traverse" }); });
    document.querySelectorAll(ARRIVEES).forEach(function (el) { scenes.push({ el: el, sorte: "arrivee" }); });

    // The quote lights up word by word. Spans only: the text reads the same.
    var citation = document.querySelector(".parole blockquote");
    if (citation) {
      parole = scenes.filter(function (s) { return s.el === citation.parentNode.parentNode; })[0];
      citation.innerHTML = citation.textContent.trim().split(/\s+/).map(function (m) {
        return '<span class="mot">' + m + "</span>";
      }).join(" ");
      mots = [].slice.call(citation.querySelectorAll(".mot"));
    }

    lu = document.createElement("div");
    lu.className = "lu";
    lu.setAttribute("aria-hidden", "true");
    document.body.appendChild(lu);

    var attend = false;
    addEventListener("scroll", function () {
      if (!glisse) plusTard();
      if (attend) return;
      attend = true;
      requestAnimationFrame(function () { attend = false; dessine(); });
    }, { passive: true });
    addEventListener("resize", mesure);
    addEventListener("load", mesure);
    if (window.ResizeObserver) new ResizeObserver(mesure).observe(document.body);
    addEventListener("pointerdown", function () { tenu = true; }, { passive: true });
    addEventListener("pointerup", function () { tenu = false; plusTard(); }, { passive: true });
    addEventListener("touchstart", function () { tenu = true; coupe(); }, { passive: true });
    addEventListener("touchend", function () { tenu = false; }, { passive: true });
    addEventListener("wheel", coupe, { passive: true });
    addEventListener("keydown", coupe);
    mesure();
  });
})();
