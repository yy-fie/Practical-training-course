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

  // 角色分权：按权限码控制左侧菜单显示
  apiRequest("/api/me/permissions")
    .then(function (r) {
      return r.ok ? r.json() : null;
    })
    .then(function (me) {
      if (!me) return;
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
      if (perms.indexOf("analysis:view") === -1) {
        var visible = null;
        document.querySelectorAll(".nav-item").forEach(function (item) {
          if (!visible && item.style.display !== "none") visible = item;
        });
        if (visible) visible.click();
      }
    })
    .catch(function () {
      /* 权限接口异常时保持默认菜单 */
    });

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
  document.getElementById("logoutBtn").addEventListener("click", function () {
    sessionStorage.removeItem("loginUser");
    window.location.href = "login.html";
  });
})();
