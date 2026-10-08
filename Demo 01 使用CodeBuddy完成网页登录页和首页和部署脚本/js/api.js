// 默认沿用当前主机；测试和部署可以提前设置 window.API_BASE。
window.API_BASE = window.API_BASE || window.location.protocol + "//" + window.location.hostname + ":9001";

/**
 * 调用 FastAPI 用户登录验证接口
 * POST /api/auth/login（JSON 请求体）
 * 成功返回用户对象；失败抛出 { status, message }
 */
async function apiLogin(username, password) {
  const resp = await fetch(API_BASE + "/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: username, password: password })
  });
  const data = await resp.json().catch(function () {
    return null;
  });

  if (!resp.ok) {
    const detail =
      data && data.detail ? data.detail : "登录失败（HTTP " + resp.status + "）";
    throw { status: resp.status, message: detail };
  }
  sessionStorage.setItem("authTokens", JSON.stringify({
    accessToken: data.accessToken, refreshToken: data.refreshToken
  }));
  return data.user;
}

/** 读取当前登录用户（Session） */
function currentUser() {
  try {
    return JSON.parse(sessionStorage.getItem("loginUser") || "null");
  } catch (e) {
    return null;
  }
}

/**
 * 带 Bearer 令牌的请求；访问令牌过期后刷新一次并重试。
 * 用法：apiRequest("/api/admin/users?page=1&rows=10", { method: "GET" })
 */
function authTokens() {
  try { return JSON.parse(sessionStorage.getItem("authTokens") || "null"); }
  catch (e) { return null; }
}

function clearSession() {
  sessionStorage.removeItem("loginUser");
  sessionStorage.removeItem("authTokens");
}

function goToLogin() {
  clearSession();
  window.top.location.href = "login.html";
}

async function refreshSession() {
  // iframe 与首页共用同一 Promise，避免并发轮换同一刷新令牌。
  var owner = window.top;
  if (!owner._authRefreshPromise) {
    owner._authRefreshPromise = (async function () {
      var tokens = authTokens();
      if (!tokens || !tokens.refreshToken) return false;
      var response = await fetch(API_BASE + "/api/auth/refresh", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refreshToken: tokens.refreshToken })
      });
      if (response.status >= 500) throw new Error('登录服务暂时不可用，请稍后重试');
      if (!response.ok) return false;
      var data = await response.json();
      sessionStorage.setItem("authTokens", JSON.stringify({
        accessToken: data.accessToken, refreshToken: data.refreshToken
      }));
      return true;
    })().finally(function () { owner._authRefreshPromise = null; });
  }
  return owner._authRefreshPromise;
}

async function apiRequest(path, options) {
  options = options || {};
  function send() {
    var headers = new Headers(options.headers || {});
    var tokens = authTokens();
    if (tokens && tokens.accessToken) headers.set("Authorization", "Bearer " + tokens.accessToken);
    return fetch(API_BASE + path, Object.assign({}, options, { headers: headers }));
  }
  var response = await send();
  if (response.status === 401) {
    if (await refreshSession()) response = await send();
    if (response.status === 401) goToLogin();
  }
  return response;
}

async function apiLogout() {
  var response = await apiRequest("/api/auth/logout", { method: "POST" });
  if (!response.ok && response.status !== 401) throw new Error("退出失败，请重试");
  goToLogin();
}
