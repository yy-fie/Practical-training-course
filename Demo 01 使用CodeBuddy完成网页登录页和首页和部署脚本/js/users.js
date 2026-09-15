(function () {
  var ADMIN_ROLES = [2, 4, 5];
  var user = currentUser();
  var perms = [];
  var page = 1;
  var rows = 10;
  var totalPages = 1;
  var roleMap = {};

  function go(url) {
    if (window.top && window.top !== window) {
      window.top.location.href = url;
    } else {
      window.location.href = url;
    }
  }

  if (!user || !user.userId) {
    go("login.html");
    return;
  }

  function show(text) {
    document.getElementById("msg").textContent = text || "";
  }

  function can(code) {
    return perms.indexOf(code) !== -1;
  }

  function loadMyPermissions() {
    return apiRequest("/api/me/permissions")
      .then(function (r) {
        if (!r.ok) throw new Error("登录信息失效，请重新登录");
        return r.json();
      })
      .then(function (data) {
        perms = data.permissions || [];
        if (!can("user:list")) {
          if (ADMIN_ROLES.indexOf(data.roleId) === -1) {
            alert("没有权限访问「用户管理」。");
          }
          go("home.html");
          throw new Error("no-permission");
        }
        window.__roleId = data.roleId;
      });
  }

  function loadRoles() {
    return apiRequest("/api/admin/roles")
      .then(function (r) {
        if (!r.ok) throw new Error("加载角色列表失败（HTTP " + r.status + "）");
        return r.json();
      })
      .then(function (data) {
        var sel = document.getElementById("kwRole");
        (data.roles || []).forEach(function (role) {
          roleMap[role.roleId] = role.roleName;
          var opt = document.createElement("option");
          opt.value = role.roleId;
          opt.textContent = role.roleName;
          sel.appendChild(opt);
        });
        document.getElementById("roleInfo").textContent =
          (user.realName || "") + "（" + (roleMap[user.roleId] || "角色" + user.roleId) + "）";
      });
  }

  function loadUsers() {
    show("");
    var params = ["page=" + page, "rows=" + rows];
    var name = document.getElementById("kwName").value.trim();
    var phone = document.getElementById("kwPhone").value.trim();
    var roleId = document.getElementById("kwRole").value;
    if (name) params.push("realName=" + encodeURIComponent(name));
    if (phone) params.push("phone=" + encodeURIComponent(phone));
    if (roleId) params.push("roleId=" + roleId);

    apiRequest("/api/admin/users?" + params.join("&"))
      .then(function (r) {
        if (r.status === 403) throw new Error("没有权限：当前账号的数据范围或权限不足");
        if (r.status === 401) throw new Error("登录信息失效，请重新登录");
        if (!r.ok) throw new Error("查询失败（HTTP " + r.status + "）");
        return r.json();
      })
      .then(function (data) {
        totalPages = Math.max(1, Math.ceil(data.total / rows));
        renderRows(data.rows || []);
        document.getElementById("pageInfo").textContent =
          "共 " + data.total + " 条，第 " + page + "/" + totalPages + " 页";
        document.getElementById("prevBtn").disabled = page <= 1;
        document.getElementById("nextBtn").disabled = page >= totalPages;
      })
      .catch(function (e) {
        if (e.message !== "no-permission") show(e.message);
      });
  }

  function renderRows(list) {
    var tbody = document.getElementById("userRows");
    tbody.innerHTML = "";
    if (!list.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#999;">没有数据</td></tr>';
      return;
    }

    list.forEach(function (u) {
      var tr = document.createElement("tr");
      var roleCell;
      if (can("role:assign")) {
        roleCell = '<select data-role-for="' + u.userId + '"></select>';
      } else {
        roleCell = roleMap[u.roleId] || ("角色" + u.roleId);
      }

      var actions = "";
      if (can("user:edit")) actions += '<button class="row-btn" data-edit="' + u.userId + '">编辑</button>';
      if (can("user:reset")) actions += '<button class="row-btn" data-reset="' + u.userId + '">重置密码</button>';
      if (can("user:delete")) actions += '<button class="row-btn danger" data-del="' + u.userId + '">删除</button>';
      if (!actions) actions = '<span style="color:#999;">—</span>';

      tr.innerHTML =
        "<td>" + u.userId + "</td>" +
        "<td>" + (u.realName || "") + "</td>" +
        "<td>" + (u.phone || "") + "</td>" +
        "<td>" + roleCell + "</td>" +
        "<td>" + (u.departmentId == null ? "" : u.departmentId) + "</td>" +
        "<td>" + (u.gender || "") + "</td>" +
        "<td>" + (u.email || "") + "</td>" +
        "<td>" + actions + "</td>";
      tbody.appendChild(tr);

      if (can("role:assign")) {
        var sel = tr.querySelector('select[data-role-for="' + u.userId + '"]');
        Object.keys(roleMap).forEach(function (rid) {
          var o = document.createElement("option");
          o.value = rid;
          o.textContent = roleMap[rid];
          if (String(u.roleId) === String(rid)) o.selected = true;
          sel.appendChild(o);
        });
        sel.addEventListener("change", function () {
          changeRole(u, sel.value);
        });
      }
    });

    tbody.querySelectorAll("button[data-edit]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-edit");
        var target = list.filter(function (x) { return String(x.userId) === String(id); })[0];
        editUser(target);
      });
    });
    tbody.querySelectorAll("button[data-reset]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        resetPassword(btn.getAttribute("data-reset"));
      });
    });
    tbody.querySelectorAll("button[data-del]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        removeUser(btn.getAttribute("data-del"));
      });
    });
  }

  function handleWrite(r) {
    return r
      .json()
      .catch(function () {
        return null;
      })
      .then(function (data) {
        if (!r.ok) throw new Error((data && data.detail) || "操作失败（HTTP " + r.status + "）");
        show("");
        loadUsers();
      });
  }

  function changeRole(u, roleId) {
    if (!roleId || String(roleId) === String(u.roleId)) return;
    if (!confirm("确定把「" + (u.realName || u.userId) + "」的角色改为「" + roleMap[roleId] + "」吗？")) {
      loadUsers();
      return;
    }
    apiRequest("/api/admin/users/" + u.userId + "/role?roleId=" + roleId, { method: "PUT" })
      .then(handleWrite)
      .catch(function (e) { show(e.message); });
  }

  function editUser(u) {
    if (!u) return;
    var realName = prompt("姓名：", u.realName || "");
    if (realName === null) return;
    var phone = prompt("手机号：", u.phone || "");
    if (phone === null) return;
    var email = prompt("邮箱：", u.email || "");
    if (email === null) return;
    apiRequest(
      "/api/admin/users/" + u.userId +
        "?realName=" + encodeURIComponent(realName) +
        "&phone=" + encodeURIComponent(phone) +
        "&email=" + encodeURIComponent(email),
      { method: "PUT" }
    )
      .then(handleWrite)
      .catch(function (e) { show(e.message); });
  }

  function resetPassword(id) {
    if (!confirm("确定把用户 " + id + " 的密码重置为 123456 吗？")) return;
    apiRequest("/api/admin/users/" + id + "/reset-password?newPassword=123456", { method: "PUT" })
      .then(handleWrite)
      .catch(function (e) { show(e.message); });
  }

  function removeUser(id) {
    if (!confirm("确定删除用户 " + id + " 吗？该操作不可恢复。")) return;
    apiRequest("/api/admin/users/" + id, { method: "DELETE" })
      .then(handleWrite)
      .catch(function (e) { show(e.message); });
  }

  document.getElementById("searchBtn").addEventListener("click", function () { page = 1; loadUsers(); });
  document.getElementById("resetBtn").addEventListener("click", function () {
    document.getElementById("kwName").value = "";
    document.getElementById("kwPhone").value = "";
    document.getElementById("kwRole").value = "";
    page = 1;
    loadUsers();
  });
  document.getElementById("prevBtn").addEventListener("click", function () { if (page > 1) { page--; loadUsers(); } });
  document.getElementById("nextBtn").addEventListener("click", function () { if (page < totalPages) { page++; loadUsers(); } });

  loadMyPermissions()
    .then(loadRoles)
    .then(loadUsers)
    .catch(function (e) { if (e.message !== "no-permission") show(e.message); });
})();