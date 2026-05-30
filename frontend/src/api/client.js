const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8002";

const TOKEN_KEY = "fraud_ai_token";
const USER_KEY = "fraud_ai_user";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function saveUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getSavedUser() {
  const raw = localStorage.getItem(USER_KEY);

  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function authHeaders() {
  const token = getToken();

  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

async function parseResponse(response) {
  let data = null;

  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const message =
      data?.detail ||
      data?.message ||
      `Request failed with status ${response.status}`;

    throw new Error(message);
  }

  return data;
}

export async function getJson(path, useAuth = true) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: useAuth ? authHeaders() : {},
  });

  return parseResponse(response);
}

export async function postJson(path, body, useAuth = false) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(useAuth ? authHeaders() : {}),
    },
    body: JSON.stringify(body),
  });

  return parseResponse(response);
}

export async function uploadCsv(file, useLlmForApproved = false) {
  const formData = new FormData();
  formData.append("file", file);

  const query = useLlmForApproved ? "?use_llm_for_approved=true" : "";

  const response = await fetch(
    `${API_BASE_URL}/uploads/predict-file${query}`,
    {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    }
  );

  return parseResponse(response);
}

export async function downloadCsv(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: authHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Download failed with status ${response.status}`);
  }

  return response.blob();
}