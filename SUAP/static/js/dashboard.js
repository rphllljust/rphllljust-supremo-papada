document.addEventListener('DOMContentLoaded', function () {
  document.body.classList.add('page-loaded');

  const internalLinks = document.querySelectorAll('a[href^="/"]');
  internalLinks.forEach(function (link) {
    link.addEventListener('click', function (event) {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) {
        return;
      }

      const href = link.getAttribute('href');
      if (!href || href === window.location.pathname) {
        return;
      }

      event.preventDefault();
      document.body.classList.remove('page-loaded');
      document.body.classList.add('page-leaving');
      setTimeout(function () {
        window.location.href = href;
      }, 170);
    });
  });

  const chartElement = document.getElementById('suapChart');
  const chartDataElement = document.getElementById('chart-data');
  if (!chartElement || !chartDataElement || typeof Chart === 'undefined') {
    return;
  }

  const rows = JSON.parse(chartDataElement.textContent || '[]');
  const labels = rows.map(function (r) { return r.school_class__name; });
  const values = rows.map(function (r) { return r.total; });

  new Chart(chartElement, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Matrículas',
        data: values,
        backgroundColor: ['#1d6f42', '#2a8753', '#3f9d66', '#56b27a', '#6dc08e']
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
    }
  });
});
