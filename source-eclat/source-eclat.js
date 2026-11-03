// The countdown of the top band. Its words are in the HTML, and they stand still without this script.
(function () {
  var band = document.querySelector(".compte");
  if (!band || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var cases = band.querySelectorAll("b");
  var left = 2 * 86400 + 14 * 3600 + 37 * 60 + 12;
  function two(n) { return (n < 10 ? "0" : "") + n; }
  setInterval(function () {
    left -= 1;
    cases[0].textContent = two(Math.floor(left / 86400));
    cases[1].textContent = two(Math.floor(left / 3600) % 24);
    cases[2].textContent = two(Math.floor(left / 60) % 60);
    cases[3].textContent = two(left % 60);
  }, 1000);
})();
