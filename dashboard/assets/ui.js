const ui = (() => {
  const qs = (selector, root = document) => root.querySelector(selector);
  const qsa = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  const el = (tag, options = {}) => {
    const node = document.createElement(tag);
    if (options.className) node.className = options.className;
    if (options.text) node.textContent = options.text;
    if (options.html) node.innerHTML = options.html;
    if (options.attrs) {
      Object.entries(options.attrs).forEach(([key, value]) => node.setAttribute(key, value));
    }
    return node;
  };

  const badge = (text, tone = "") => {
    const node = el("span", { className: `badge ${tone}`.trim(), text });
    return node;
  };

  const toast = (message, tone = "") => {
    const node = el("div", { className: `toast ${tone}`.trim(), text: message });
    document.body.appendChild(node);
    setTimeout(() => node.remove(), 3500);
  };

  const formatDateTime = (value) => {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
  };

  const formatNumber = (value) => {
    if (value === null || value === undefined) return "-";
    if (typeof value === "number") return value.toLocaleString();
    return value;
  };

  const renderList = (container, items, emptyMessage = "データがありません") => {
    container.innerHTML = "";
    if (!items || items.length === 0) {
      container.appendChild(el("div", { className: "notice", text: emptyMessage }));
      return;
    }
    items.forEach((item) => container.appendChild(item));
  };

  const renderNotImplementedBanner = (target, detail = "") => {
    if (!target) return null;
    target.innerHTML = "";
    const node = el("div", {
      className: "notice warning",
      text: "未実装：バックエンドAPIが存在しません",
    });
    if (detail) {
      node.appendChild(el("div", { className: "muted", text: detail }));
    }
    target.appendChild(node);
    return node;
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      toast("コピーしました", "success");
    } catch (_error) {
      toast("コピーに失敗しました", "warning");
    }
  };

  const applyCapabilitiesToNav = (capabilities) => {
    if (!capabilities || !capabilities.features) return;
    qsa(".top-nav a[data-feature]").forEach((link) => {
      const featureKey = link.dataset.feature;
      if (!featureKey) return;
      if (!window.app || !window.app.isFeatureEnabled) return;
      if (!window.app.isFeatureEnabled(capabilities, featureKey)) {
        link.style.display = "none";
      }
    });
  };

  return {
    qs,
    qsa,
    el,
    badge,
    toast,
    formatDateTime,
    formatNumber,
    renderList,
    renderNotImplementedBanner,
    copyToClipboard,
    applyCapabilitiesToNav,
  };
})();

window.ui = ui;
