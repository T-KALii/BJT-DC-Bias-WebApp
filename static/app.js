// Show an honest in-flight state while Flask calls the external solver.
// The numeric result is never produced here; it only changes a status label.
document.addEventListener("DOMContentLoaded", function () {
  var status = document.getElementById("run-status");
  if (!status) return;

  document.querySelectorAll("form[action='/simulator/run']").forEach(function (form) {
    form.addEventListener("submit", function () {
      status.textContent = "RUNNING · ngspice";
      status.className = "sim-status status-running";
    });
  });
});
