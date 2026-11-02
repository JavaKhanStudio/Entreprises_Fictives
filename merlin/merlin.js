/* Papeterie Merlin: the 3D paperclip, the counters, the reveals. A classic script, not a module:
   over file:// a browser refuses modules, and a page must open by double-click. Nothing here is
   fetched, and every word of the site is already in the HTML: without this file, or without
   WebGL, a reader loses the show and none of the text. */
(function () {
  "use strict";
  var calme = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* The wire's centre line: three U-turns, like a real clip. Same drawing as img/trombone.svg. */
  function ligne() {
    var points = [];
    function droite(x, y0, y1) {
      var n = Math.ceil(Math.abs(y1 - y0) / 2);
      for (var i = 0; i < n; i++) points.push([x, y0 + (y1 - y0) * i / n]);
    }
    function arc(cx, cy, r, debut, fin) {
      var n = 28;
      for (var i = 0; i < n; i++) {
        var a = debut + (fin - debut) * i / n;
        points.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
      }
    }
    var pi = Math.PI;
    droite(36, 26, 68);
    arc(47, 68, 11, pi, 0);
    droite(58, 68, 22);
    arc(50, 22, 8, 0, -pi);
    droite(42, 22, 66);
    arc(46, 66, 4, pi, 0);
    droite(50, 66, 30);
    points.push([50, 30]);
    return points.map(function (p, i) {
      var t = i / (points.length - 1);
      /* Centred, y up, with a slight twist out of the plane: no real clip lies quite flat. */
      return [(p[0] - 47) / 30, (45 - p[1]) / 30, 0.09 * Math.sin(t * Math.PI * 3)];
    });
  }

  /* A tube around that line: rings carried along without twisting, closed by rounded ends. */
  function tube(points, rayon, cotes) {
    var positions = [], normales = [], indices = [];
    var n = [0, 0, 1];
    points.forEach(function (p, i) {
      var a = points[Math.max(i - 1, 0)], b = points[Math.min(i + 1, points.length - 1)];
      var t = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
      var l = Math.hypot(t[0], t[1], t[2]);
      t = [t[0] / l, t[1] / l, t[2] / l];
      var d = n[0] * t[0] + n[1] * t[1] + n[2] * t[2];
      n = [n[0] - d * t[0], n[1] - d * t[1], n[2] - d * t[2]];
      l = Math.hypot(n[0], n[1], n[2]);
      n = [n[0] / l, n[1] / l, n[2] / l];
      var m = [t[1] * n[2] - t[2] * n[1], t[2] * n[0] - t[0] * n[2], t[0] * n[1] - t[1] * n[0]];
      var bout = Math.min(i, points.length - 1 - i);
      var r = bout < 3 ? rayon * Math.sqrt(1 - Math.pow((3 - bout) / 3.2, 2)) : rayon;
      for (var c = 0; c < cotes; c++) {
        var q = c / cotes * Math.PI * 2, x = Math.cos(q), y = Math.sin(q);
        var v = [n[0] * x + m[0] * y, n[1] * x + m[1] * y, n[2] * x + m[2] * y];
        positions.push(p[0] + v[0] * r, p[1] + v[1] * r, p[2] + v[2] * r);
        normales.push(v[0], v[1], v[2]);
      }
    });
    for (var i = 0; i < points.length - 1; i++) {
      for (var c = 0; c < cotes; c++) {
        var a = i * cotes + c, b = i * cotes + (c + 1) % cotes;
        var e = a + cotes, f = b + cotes;
        indices.push(a, e, b, b, e, f);
      }
    }
    return { positions: new Float32Array(positions), normales: new Float32Array(normales), indices: new Uint16Array(indices) };
  }

  var SOMMETS = [
    "attribute vec3 position; attribute vec3 normale;",
    "uniform mat4 monde; uniform float aspect; varying vec3 vN; varying vec3 vP;",
    "void main() {",
    "  vec4 p = monde * vec4(position, 1.0); vN = mat3(monde) * normale; vP = p.xyz;",
    "  float w = 3.4 - p.z;",
    "  float k = 2.5; gl_Position = vec4(p.x * k * min(1.0, 1.0 / aspect), p.y * k * min(1.0, aspect), -p.z * 0.1 * w, w);",
    "}"
  ].join("\n");

  /* Polished steel: no texture, what it reflects is a studio worked out on the spot. */
  var PIXELS = [
    "precision highp float; varying vec3 vN; varying vec3 vP;",
    "vec3 studio(vec3 r) {",
    "  float h = r.y * 0.5 + 0.5;",
    "  vec3 c = mix(vec3(0.04, 0.05, 0.13), vec3(0.62, 0.66, 0.82), smoothstep(0.1, 1.0, h));",
    "  c += vec3(1.5, 1.45, 1.4) * smoothstep(0.72, 0.9, r.y) * smoothstep(0.9, 0.2, abs(r.x));",
    "  c += vec3(0.62, 0.34, 1.25) * smoothstep(0.35, 0.95, -r.x) * smoothstep(0.9, 0.0, abs(r.y));",
    "  c += vec3(1.25, 0.4, 0.55) * smoothstep(0.45, 0.98, r.x) * smoothstep(0.8, 0.0, abs(r.y + 0.15));",
    "  c += vec3(0.9) * smoothstep(0.93, 0.985, r.z) * smoothstep(0.3, 0.05, abs(r.y - 0.25));",
    "  return c;",
    "}",
    "void main() {",
    "  vec3 n = normalize(vN), v = normalize(vec3(0.0, 0.0, 3.4) - vP);",
    "  vec3 r = reflect(-v, n);",
    "  float f = pow(1.0 - max(dot(n, v), 0.0), 4.0);",
    "  vec3 c = studio(r) * mix(0.82, 1.0, f) + vec3(0.25, 0.27, 0.36) * f;",
    "  c = c / (1.0 + c * 0.35);",
    "  gl_FragColor = vec4(pow(c, vec3(0.86)), 1.0);",
    "}"
  ].join("\n");

  function trombone(toile, repli) {
    var gl = null;
    try {
      gl = toile.getContext("webgl", { alpha: true, antialias: true, premultipliedAlpha: true });
    } catch (e) { gl = null; }
    if (!gl) return;

    function nuanceur(type, source) {
      var s = gl.createShader(type);
      gl.shaderSource(s, source);
      gl.compileShader(s);
      return s;
    }
    var prog = gl.createProgram();
    gl.attachShader(prog, nuanceur(gl.VERTEX_SHADER, SOMMETS));
    gl.attachShader(prog, nuanceur(gl.FRAGMENT_SHADER, PIXELS));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return;
    gl.useProgram(prog);

    var forme = tube(ligne(), 0.058, 18);
    function attribut(nom, donnees) {
      gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
      gl.bufferData(gl.ARRAY_BUFFER, donnees, gl.STATIC_DRAW);
      var a = gl.getAttribLocation(prog, nom);
      gl.enableVertexAttribArray(a);
      gl.vertexAttribPointer(a, 3, gl.FLOAT, false, 0, 0);
    }
    attribut("position", forme.positions);
    attribut("normale", forme.normales);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, forme.indices, gl.STATIC_DRAW);
    gl.enable(gl.DEPTH_TEST);
    gl.clearColor(0, 0, 0, 0);
    var monde = gl.getUniformLocation(prog, "monde");
    var aspect = gl.getUniformLocation(prog, "aspect");

    /* The angle a still picture shows, and where the turning starts from. */
    var lacet = 0.6, tangage = -0.14, inertie = 0.5, tire = false, vu = true;
    var dernier = 0, debut = 0;

    function dessine(t) {
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      var l = Math.round(toile.clientWidth * dpr), h = Math.round(toile.clientHeight * dpr);
      if (!l || !h) return;
      if (toile.width !== l || toile.height !== h) { toile.width = l; toile.height = h; }
      gl.viewport(0, 0, l, h);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      var flotte = calme ? 0 : Math.sin(t / 1400) * 0.05;
      var roulis = calme ? 0.2 : 0.2 + Math.sin(t / 2300) * 0.05;
      var cy = Math.cos(lacet), sy = Math.sin(lacet);
      var cx = Math.cos(tangage), sx = Math.sin(tangage);
      var cz = Math.cos(roulis), sz = Math.sin(roulis);
      /* Roll, then yaw, then pitch, column by column. */
      gl.uniformMatrix4fv(monde, false, new Float32Array([
        cz * cy, sz * cx + cz * sy * sx, sz * sx - cz * sy * cx, 0,
        -sz * cy, cz * cx - sz * sy * sx, cz * sx + sz * sy * cx, 0,
        sy, -cy * sx, cy * cx, 0,
        0, flotte, 0, 1
      ]));
      gl.uniform1f(aspect, l / h);
      gl.drawElements(gl.TRIANGLES, forme.indices.length, gl.UNSIGNED_SHORT, 0);
    }

    function image(t) {
      if (!dernier) { dernier = t; debut = t; }
      var dt = Math.min(t - dernier, 50) / 1000;
      dernier = t;
      if (!tire) {
        lacet += inertie * dt;
        inertie += (0.5 - inertie) * Math.min(dt * 1.2, 1);
      }
      if (vu) dessine(t - debut);
      window.requestAnimationFrame(image);
    }

    var x0 = 0, y0 = 0;
    toile.addEventListener("pointerdown", function (e) {
      tire = true; x0 = e.clientX; y0 = e.clientY;
      toile.setPointerCapture(e.pointerId);
    });
    toile.addEventListener("pointermove", function (e) {
      if (!tire) return;
      var dx = (e.clientX - x0) * 0.01;
      lacet += dx;
      tangage = Math.max(-0.9, Math.min(0.9, tangage + (e.clientY - y0) * 0.006));
      inertie = dx * 40;
      x0 = e.clientX; y0 = e.clientY;
      if (calme) dessine(0);
    });
    function lache() { tire = false; }
    toile.addEventListener("pointerup", lache);
    toile.addEventListener("pointercancel", lache);
    toile.addEventListener("webglcontextlost", function () { toile.hidden = true; repli.hidden = false; });

    toile.hidden = false;
    repli.hidden = true;
    var astuce = document.querySelector(".astuce");
    if (astuce) astuce.hidden = false;
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (v) { vu = v[0].isIntersecting; }).observe(toile);
    }
    if ("ResizeObserver" in window && calme) {
      new ResizeObserver(function () { dessine(0); }).observe(toile);
    }
    if (calme) dessine(0);
    else window.requestAnimationFrame(image);
  }

  var toile = document.getElementById("trombone");
  if (toile) trombone(toile, document.getElementById("trombone-repli"));

  /* The current page's entry stays in view in the phone's sliding menu. */
  var courant = document.querySelector(".tete nav [aria-current]");
  if (courant) {
    var menu = courant.closest("ul");
    menu.scrollLeft = courant.offsetLeft - (menu.clientWidth - courant.offsetWidth) / 2;
  }

  /* The light that follows the pointer across a card. */
  document.querySelectorAll(".carte").forEach(function (carte) {
    carte.addEventListener("pointermove", function (e) {
      var r = carte.getBoundingClientRect();
      carte.style.setProperty("--x", (e.clientX - r.left) + "px");
      carte.style.setProperty("--y", (e.clientY - r.top) + "px");
    });
  });

  if (calme || !("IntersectionObserver" in window)) return;

  /* Counters climb to the number the HTML already holds. */
  var observe = new IntersectionObserver(function (vus) {
    vus.forEach(function (v) {
      if (!v.isIntersecting) return;
      observe.unobserve(v.target);
      var el = v.target, fin = parseInt(el.textContent, 10), t0 = 0;
      function pas(t) {
        if (!t0) t0 = t;
        var k = Math.min((t - t0) / 1400, 1);
        el.textContent = String(Math.round(fin * (1 - Math.pow(1 - k, 4))));
        if (k < 1) window.requestAnimationFrame(pas);
      }
      window.requestAnimationFrame(pas);
    });
  }, { threshold: 0.6 });
  document.querySelectorAll(".chiffres strong").forEach(function (el) { observe.observe(el); });

  /* Sections rise into place, once. */
  var monte = new IntersectionObserver(function (vus) {
    vus.forEach(function (v) {
      if (v.isIntersecting) { v.target.classList.add("vu"); monte.unobserve(v.target); }
    });
  }, { rootMargin: "0px 0px -8% 0px" });
  document.querySelectorAll("main > section:not(.une), main > .arbre").forEach(function (el) {
    el.classList.add("monte");
    monte.observe(el);
  });
})();
