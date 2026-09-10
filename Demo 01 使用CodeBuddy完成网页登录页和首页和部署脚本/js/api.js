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
