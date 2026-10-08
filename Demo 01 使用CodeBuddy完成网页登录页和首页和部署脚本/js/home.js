(function () {
  // 读取 Session 中的登录用户；未登录则回到登录页
  var raw = sessionStorage.getItem("loginUser");
  var user = null;
  try {
    user = raw ? JSON.parse(raw) : null;
  } catch (e) {
    user = null;
  }

  if (!user) {
    window.location.href = "login.html";
    return;
  }

  var name = user.realName || user.phone || "用户";
  document.querySelectorAll('.nav-item').forEach(function (item) { item.style.display = 'none'; });
  document.getElementById('contentFrame').src = 'about:blank';

  // 角色分权：按权限码控制左侧菜单显示
  function loadPermissions() { return apiRequest("/api/me/permissions")
    .then(function (r) {
      return r.ok ? r.json() : null;
    })
    .then(function (me) {
      if (!me) throw new Error('权限加载失败，请重新登录');
      var perms = me.permissions || [];

      function showNav(id, code) {
        var el = document.getElementById(id);
        if (!el) return;
        el.style.display = perms.indexOf(code) === -1 ? "none" : "";
      }

      showNav("nav-analysis1", "analysis:view");
      showNav("nav-analysis2", "analysis:view");
      showNav("nav-password", "password:self");
      showNav("nav-profile", "profile:self");
      showNav("nav-users", "user:list");
      showNav("nav-perms", "permission:manage");
      showNav("nav-grants", "role:assign");

      // 若当前默认页无权限，自动切到第一个可见菜单
      var active = document.querySelector('.nav-item.active');
      if (!active || active.style.display === 'none' || document.getElementById('contentFrame').getAttribute('src') === 'about:blank') {
        var visible = null;
        document.querySelectorAll(".nav-item").forEach(function (item) {
          if (!visible && item.style.display !== "none") visible = item;
        });
        if (visible) visible.click();
        else {
          document.getElementById('contentFrame').src = 'about:blank';
          document.getElementById('pageTitle').textContent = '当前账号暂无可用菜单';
        }
      }
    })
    .catch(function (error) {
      document.querySelectorAll('.nav-item').forEach(function (item) { item.style.display = 'none'; });
      document.getElementById('contentFrame').src = 'about:blank';
      document.getElementById('pageTitle').textContent = error.message || '权限加载失败，请刷新重试';
    }); }

  // 左下角显示真实姓名
  document.getElementById("userName").textContent = name;
  document.getElementById("userAvatar").textContent =
    name.trim().charAt(0) || "用";
  var meta = user.phone || "";
  if (user.email) {
    meta += meta ? " · " + user.email : user.email;
  }
  document.getElementById("userMeta").textContent = meta || "已登录";

  // 左侧导航：右侧 iframe 切换分析页面
  var navItems = document.querySelectorAll(".nav-item");
  var frame = document.getElementById("contentFrame");
  var titleEl = document.getElementById("pageTitle");

  navItems.forEach(function (item) {
    item.addEventListener("click", function (e) {
      e.preventDefault();
      navItems.forEach(function (x) {
        x.classList.remove("active");
      });
      item.classList.add("active");
      frame.src = item.getAttribute("data-page");
      titleEl.textContent = item.getAttribute("data-title");
    });
  });

  // 退出：清除 Session 并回到登录页
  document.getElementById("logoutBtn").addEventListener("click", async function () {
    this.disabled = true;
    try { await apiLogout(); }
    catch (error) { document.getElementById('pageTitle').textContent = error.message || '退出失败，请重试'; }
    finally { this.disabled = false; }
  });
  loadPermissions();
  setInterval(loadPermissions, 60000);
  window.addEventListener('focus', loadPermissions);
})();
