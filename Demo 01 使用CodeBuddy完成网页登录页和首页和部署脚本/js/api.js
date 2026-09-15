// FastAPI 接口地址（Demo 02 FastAPI 项目默认运行在 9001 端口）
window.API_BASE = "http://127.0.0.1:9001";

/**
 * 调用 FastAPI 用户登录验证接口
 * POST /api/users/login?username=xxx&password=xxx
 * 成功返回用户对象；失败抛出 { status, message }
 */
async function apiLogin(username, password) {
  const url =
    API_BASE +
    "/api/users/login?username=" +
    encodeURIComponent(username) +
    "&password=" +
    encodeURIComponent(password);

  const resp = await fetch(url, { method: "POST" });
  const data = await resp.json().catch(function () {
    return null;
  });

  if (!resp.ok) {
    const detail =
      data && data.detail ? data.detail : "登录失败（HTTP " + resp.status + "）";
    throw { status: resp.status, message: detail };
  }
  return data;
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
 * 带权限信息的请求封装：自动附加 X-User-Id 请求头
 * 用法：apiRequest("/api/admin/users?page=1&rows=10", { method: "GET" })
 */
function apiRequest(path, options) {
  options = options || {};
  var headers = options.headers || {};
  var user = currentUser();
  if (user && user.userId) {
    headers["X-User-Id"] = String(user.userId);
  }
  options.headers = headers;
  return fetch(API_BASE + path, options);
}
