const storage = (() => {
  const STORAGE_BASE = "JAVIS_API_BASE";
  const STORAGE_TOKEN = "JAVIS_API_TOKEN";

  const getItem = (key) => (localStorage.getItem(key) || "").trim();
  const setItem = (key, value) => {
    const trimmed = (value || "").trim();
    if (trimmed) {
      localStorage.setItem(key, trimmed);
    } else {
      localStorage.removeItem(key);
    }
  };

  const getApiBase = () => getItem(STORAGE_BASE);
  const getApiToken = () => getItem(STORAGE_TOKEN);

  const setApiConfig = (base, token) => {
    setItem(STORAGE_BASE, base);
    setItem(STORAGE_TOKEN, token);
  };

  const clearApiConfig = () => {
    localStorage.removeItem(STORAGE_BASE);
    localStorage.removeItem(STORAGE_TOKEN);
  };

  return {
    STORAGE_BASE,
    STORAGE_TOKEN,
    getApiBase,
    getApiToken,
    setApiConfig,
    clearApiConfig,
  };
})();

window.storage = storage;
