(function () {
  var todayEl = document.getElementById("today");
  if (todayEl) {
    var d = new Date();
    todayEl.textContent =
      d.getFullYear() +
      "-" +
      String(d.getMonth() + 1).padStart(2, "0") +
      "-" +
      String(d.getDate()).padStart(2, "0");
  }
})();
