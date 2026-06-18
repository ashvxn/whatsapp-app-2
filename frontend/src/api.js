import axios from "axios";

// Use localhost only when actually running locally, otherwise point to the backend
// configured via VITE_API_BASE_URL (update frontend/.env when the tunnel URL changes)
const isDev = window.location.hostname === "localhost";
const baseURL = isDev ? "http://localhost:5006" : import.meta.env.VITE_API_BASE_URL;

const instance = axios.create({
  baseURL: `${baseURL}/api`
});

instance.interceptors.request.use(config => {
  const token = localStorage.getItem("amd_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

instance.interceptors.response.use(
  res => res,
  err => {
    if (err.response && err.response.status === 401) {
      localStorage.removeItem("amd_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export default instance;
export { baseURL };
