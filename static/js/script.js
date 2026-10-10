document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const themeButton = document.getElementById("themeToggle");
  if (themeButton) {
    themeButton.addEventListener("click", async () => {
      const next = root.dataset.theme === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try {
        const form = new FormData();
        form.append("theme", next);
        await fetch("/settings", { method: "POST", body: form });
      } catch (e) {}
    });
  }

  const overlay = document.getElementById("searchOverlay");
  const searchButton = document.getElementById("globalSearchButton");
  const overlayInput = document.getElementById("overlaySearch");
  function openSearch() {
    if (!overlay) return;
    overlay.classList.add("visible");
    setTimeout(() => overlayInput && overlayInput.focus(), 30);
  }
  function closeSearch() { if (overlay) overlay.classList.remove("visible"); }
  if (searchButton) searchButton.addEventListener("click", openSearch);
  if (overlay) overlay.addEventListener("click", e => { if (e.target === overlay) closeSearch(); });
  if (overlayInput) overlayInput.addEventListener("keydown", e => {
    if (e.key === "Enter") window.location.href = "/employees?q=" + encodeURIComponent(overlayInput.value);
  });

  document.addEventListener("keydown", e => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openSearch(); }
    if (e.key === "Escape") closeSearch();
    if (e.altKey && e.key.toLowerCase() === "d") { e.preventDefault(); window.location.href = "/dashboard"; }
    if (e.altKey && e.key.toLowerCase() === "a") { e.preventDefault(); window.location.href = "/employees/add"; }
  });

  document.querySelectorAll("[data-toggle-password]").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.dataset.togglePassword);
      if (!input) return;
      input.type = input.type === "password" ? "text" : "password";
      btn.textContent = input.type === "password" ? "Show" : "Hide";
    });
  });

  const mobileMenu = document.getElementById("mobileMenu");
  const sidebar = document.getElementById("sidebar");
  if (mobileMenu && sidebar) mobileMenu.addEventListener("click", () => sidebar.classList.toggle("sidebar-open"));

  const palette = ["#7165e3", "#31b58a", "#f5a64a", "#4c9be8", "#e76d93", "#9c78cf", "#7c8b9e"];
  const textColor = getComputedStyle(root).getPropertyValue("--muted").trim() || "#778096";
  const gridColor = getComputedStyle(root).getPropertyValue("--border").trim() || "#e7eaf1";
  function makeBar(id, labels, values) {
    const el = document.getElementById(id);
    if (!el || !labels || !labels.length) return;
    new Chart(el, {type:"bar",data:{labels,datasets:[{label:"Employees",data:values,backgroundColor:labels.map((_,i)=>palette[i%palette.length]),borderRadius:7,maxBarThickness:42}]},
      options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{color:textColor}},y:{beginAtZero:true,ticks:{precision:0,color:textColor},grid:{color:gridColor}}}}});
  }
  function makeDoughnut(id, labels, values) {
    const el = document.getElementById(id);
    if (!el || !labels || !labels.length) return;
    new Chart(el, {type:"doughnut",data:{labels,datasets:[{data:values,backgroundColor:palette,borderWidth:0,hoverOffset:7}]},
      options:{responsive:true,maintainAspectRatio:false,cutout:"68%",plugins:{legend:{position:"bottom",labels:{usePointStyle:true,boxWidth:7,padding:18,color:textColor}}}}});
  }
  if (window.dashboardData) {
    makeBar("departmentChart", window.dashboardData.departments, window.dashboardData.departmentCounts);
    makeDoughnut("statusChart", window.dashboardData.statuses, window.dashboardData.statusCounts);
  }
  if (window.reportData) {
    makeBar("reportDepartmentChart", window.reportData.departments, window.reportData.departmentCounts);
    makeDoughnut("reportStatusChart", window.reportData.statuses, window.reportData.statusCounts);
  }
});
