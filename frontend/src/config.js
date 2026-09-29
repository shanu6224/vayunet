export const API_URL =
  (import.meta.env && import.meta.env.VITE_API_URL) ||
  localStorage.getItem("VAYUNET_API_URL") ||
  (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : `${window.location.protocol}//${window.location.hostname}:8000`);
