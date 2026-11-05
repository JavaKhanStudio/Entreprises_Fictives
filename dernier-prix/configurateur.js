// Press on the coffin and drag: it turns with the pointer, a full turn for the scene's width, and stops on release.
// Nothing moves without a press. The radios stay what chooses: a view or an arrow key takes the drag's angle off.
(function () {
  var scene = document.querySelector('.scene');
  var plateau = scene.querySelector('.plateau');
  var from = null;

  function shown() {
    var m = new DOMMatrix(getComputedStyle(plateau).transform);
    return Math.atan2(-m.m13, m.m11) * 180 / Math.PI;
  }

  function set(angle) {
    plateau.style.setProperty('--a', (((angle + 180) % 360 + 360) % 360 - 180) + 'deg');
  }

  function release() {
    plateau.style.removeProperty('--a');
  }

  function stop() {
    from = null;
    scene.classList.remove('prise');
  }

  scene.classList.add('saisie');
  scene.addEventListener('pointerdown', function (e) {
    if (e.button !== 0) return;
    from = { x: e.clientX, angle: shown() };
    set(from.angle);
    scene.classList.add('prise', 'tenue');
    scene.setPointerCapture(e.pointerId);
  });
  scene.addEventListener('pointermove', function (e) {
    if (from) set(from.angle + (e.clientX - from.x) * 360 / scene.clientWidth);
  });
  scene.addEventListener('pointerup', stop);
  scene.addEventListener('pointercancel', stop);
  document.addEventListener('change', function (e) {
    if (e.target.name === 'vue') release();
  });
  document.querySelector('.vues').addEventListener('click', function (e) {
    if (e.target.hasAttribute('for')) release();
  });
})();
