const config = require('../config');
const STORAGE_KEY = 'metro.session';
let refreshPromise = null;
let generation = 0;
let redirecting = false;

function session() { return wx.getStorageSync(STORAGE_KEY) || null; }
function store(value) { wx.setStorageSync(STORAGE_KEY, value); }
function clearSession() { generation += 1; wx.removeStorageSync(STORAGE_KEY); }
function errorMessage(data, fallback) {
  if (data && typeof data.detail === 'string') return data.detail;
  if (data && Array.isArray(data.detail)) return data.detail.map(item => item.msg).join('；');
  return fallback;
}
function failure(message, status) { const error = new Error(message); error.status = status; return error; }
function send(path, options, token) {
  return new Promise((resolve, reject) => {
    const header = Object.assign({ 'Content-Type': 'application/json' }, options.header || {});
    if (token) header.Authorization = 'Bearer ' + token;
    wx.request({
      url: config.apiBase.replace(/\/$/, '') + path,
      method: options.method || 'GET', data: options.data, header, timeout: 15000,
      success: resolve,
      fail: () => reject(failure('暂时无法连接服务，请稍后重试', 0))
    });
  });
}
function redirectLogin() {
  if (redirecting) return;
  redirecting = true;
  wx.reLaunch({ url: '/pages/login/login', complete: () => { redirecting = false; } });
}
function requireSession() {
  const current = session();
  if (!current || !current.accessToken || !current.user) { redirectLogin(); return false; }
  return true;
}
async function refresh() {
  if (!refreshPromise) {
    const current = session();
    const expectedGeneration = generation;
    refreshPromise = (async () => {
      if (!current || !current.refreshToken) return false;
      const result = await send('/api/auth/refresh', { method: 'POST', data: { refreshToken: current.refreshToken } });
      if (result.statusCode >= 500) throw failure('登录服务暂时不可用，请稍后重试', result.statusCode);
      if (result.statusCode !== 200) return false;
      const latest = session();
      if (generation !== expectedGeneration || !latest || latest.refreshToken !== current.refreshToken) return false;
      store(Object.assign({}, latest, { accessToken: result.data.accessToken, refreshToken: result.data.refreshToken }));
      return true;
    })().finally(() => { refreshPromise = null; });
  }
  return refreshPromise;
}
async function request(path, options = {}) {
  const current = session();
  const expectedGeneration = generation;
  if (!current || !current.accessToken) { redirectLogin(); throw failure('请先登录', 401); }
  let result = await send(path, options, current.accessToken);
  if (generation !== expectedGeneration) throw failure('登录状态已变化，请重试', 401);
  if (result.statusCode === 401) {
    const renewed = await refresh();
    if (generation !== expectedGeneration) throw failure('登录状态已变化，请重试', 401);
    if (renewed) {
      result = await send(path, options, session().accessToken);
    }
    if (result.statusCode === 401) { clearSession(); redirectLogin(); }
  }
  if (generation !== expectedGeneration && result.statusCode !== 401) throw failure('登录状态已变化，请重试', 401);
  if (result.statusCode < 200 || result.statusCode >= 300) {
    throw failure(errorMessage(result.data, '请求失败，请重试'), result.statusCode);
  }
  return result.data;
}
async function login(username, password) {
  const result = await send('/api/auth/login', { method: 'POST', data: { username, password } });
  if (result.statusCode !== 200) throw failure(errorMessage(result.data, '登录失败'), result.statusCode);
  generation += 1;
  store({ user: result.data.user, accessToken: result.data.accessToken, refreshToken: result.data.refreshToken });
  return result.data.user;
}
async function permissions() {
  const me = await request('/api/me/permissions');
  getApp().globalData.permissions = me.permissions || [];
  return me;
}
function hasPermission(code) { return (getApp().globalData.permissions || []).indexOf(code) !== -1; }
function updateUser(user) { const current = session(); if (current) store(Object.assign({}, current, { user })); }
async function logout() { await request('/api/auth/logout', { method: 'POST' }); clearSession(); redirectLogin(); }
function query(values) {
  const parts = Object.keys(values).filter(key => values[key] !== '' && values[key] != null)
    .map(key => encodeURIComponent(key) + '=' + encodeURIComponent(values[key]));
  return parts.length ? '?' + parts.join('&') : '';
}
module.exports = { session, clearSession, requireSession, request, login, permissions, hasPermission, updateUser, logout, query };
