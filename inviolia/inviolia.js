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

  document.addEventListener("DOMContentLoaded", function () {
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
