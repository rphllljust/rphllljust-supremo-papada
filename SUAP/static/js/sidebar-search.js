document.addEventListener("DOMContentLoaded", function () {
  const input = document.querySelector("[data-sidebar-search-input]");
  const nav = document.querySelector("[data-sidebar-nav]");
  const emptyState = document.querySelector("[data-sidebar-search-empty]");

  if (!input || !nav) {
    return;
  }

  const topNodes = Array.from(nav.children);

  nav.querySelectorAll("details").forEach((details) => {
    details.dataset.defaultOpen = details.open ? "true" : "false";
  });

  function matchesText(text, query) {
    return text.toLowerCase().includes(query);
  }

  function resetDetailsState(container) {
    container.querySelectorAll("details").forEach((details) => {
      details.open = details.dataset.defaultOpen === "true";
    });
  }

  function showAllBranch(container) {
    container.hidden = false;

    const descendants = container.querySelectorAll(".sidebar-tree-item, .sidebar-group, .sidebar-link");
    descendants.forEach((item) => {
      item.hidden = false;
    });

    container.querySelectorAll("details").forEach((details) => {
      details.open = true;
    });
  }

  function filterTreeItem(item, query) {
    const nestedDetails = item.querySelector(":scope > details.sidebar-collapsible-item");
    const directLink = item.querySelector(":scope > a.sidebar-tree-link");

    if (nestedDetails) {
      const summary = nestedDetails.querySelector(":scope > summary.sidebar-tree-link");
      const summaryMatch = matchesText(summary.textContent.trim(), query);
      const children = Array.from(nestedDetails.querySelectorAll(":scope > ul > li.sidebar-tree-item"));

      let childMatch = false;
      children.forEach((child) => {
        if (summaryMatch) {
          showAllBranch(child);
          childMatch = true;
        } else if (filterTreeItem(child, query)) {
          childMatch = true;
        }
      });

      const visible = summaryMatch || childMatch;
      item.hidden = !visible;
      nestedDetails.open = visible;
      return visible;
    }

    if (directLink) {
      const visible = matchesText(directLink.textContent.trim(), query);
      item.hidden = !visible;
      return visible;
    }

    item.hidden = false;
    return false;
  }

  function filterGroup(group, query) {
    const details = group.querySelector(":scope > details.sidebar-collapsible");
    const summary = details.querySelector(":scope > summary.sidebar-group-title");
    const summaryMatch = matchesText(summary.textContent.trim(), query);
    const children = Array.from(details.querySelectorAll(":scope > ul > li.sidebar-tree-item"));

    let childMatch = false;
    children.forEach((child) => {
      if (summaryMatch) {
        showAllBranch(child);
        childMatch = true;
      } else if (filterTreeItem(child, query)) {
        childMatch = true;
      }
    });

    const visible = summaryMatch || childMatch;
    group.hidden = !visible;
    details.open = visible;
    return visible;
  }

  function filterTopNode(node, query) {
    if (node.classList.contains("sidebar-link")) {
      const visible = matchesText(node.textContent.trim(), query);
      node.hidden = !visible;
      return visible;
    }

    if (node.classList.contains("sidebar-group")) {
      return filterGroup(node, query);
    }

    node.hidden = false;
    return false;
  }

  function applyFilter() {
    const query = input.value.trim().toLowerCase();

    if (!query) {
      topNodes.forEach((node) => {
        node.hidden = false;
        resetDetailsState(node);
        node.querySelectorAll(".sidebar-tree-item").forEach((item) => {
          item.hidden = false;
        });
      });

      if (emptyState) {
        emptyState.hidden = true;
      }
      return;
    }

    let visibleCount = 0;
    topNodes.forEach((node) => {
      if (filterTopNode(node, query)) {
        visibleCount += 1;
      }
    });

    if (emptyState) {
      emptyState.hidden = visibleCount > 0;
    }
  }

  input.addEventListener("input", applyFilter);
});