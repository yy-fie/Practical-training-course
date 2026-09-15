(function () {
  function go(url) {
    if (window.top && window.top !== window) {
      window.top.location.href = url;
    } else {
      window.location.href = url;
    }
  }

  function show(text) {
    document.getElementById("msg").textContent = text || "";
  }

  var page = 1;
  var rows = 10;
  var totalPages = 1;

  apiRequest("/api/me/permissions")
    .then(function (r) {
      if (!r.ok) throw new Error("登录信息失效，请重新登录");
      return r.json();
    })
    .then(function (me) {
      if ((me.permissions || []).indexOf("role:assign") === -1) {
        alert("当前账号没有授权权限。");
        go("home.html");
        throw new Error("no-permission");
      }
      document.getElementById("whoami").textContent = me.realName || "";
      loadScope();
    })
    .catch(function (e) {
      if (e.message !== "no-permission") show(e.message);
    });

  function loadScope() {
    apiRequest("/api/admin/grants/scope")
      .then(function (r) {
        if (!r.ok) throw new Error("加载可授权角色失败（HTTP " + r.status + "）");
        return r.json();
      })
      .then(function (data) {
        var sel = document.getElementById("grantRoleId");
        sel.innerHTML = "";
        (data.roles || []).forEach(function (role) {
          var o = document.createElement("option");
          o.value = role.roleId;
          o.textContent = role.roleName;
          sel.appendChild(o);
        });
        if (!data.roles || !data.roles.length) {
          sel.innerHTML = '<option value="">无可授权角色</option>';
        }
        loadGrants();
      })
      .catch(function (e) { show(e.message); });
  }

  function statusText(s) {
    if (s === "active") return "生效中";
    if (s === "revoked") return "已撤销";
    if (s === "expired") return "已过期";
    return s || "";
  }

  function loadGrants() {
    show("");
    var params = ["page=" + page, "rows=" + rows];
    var uid = document.getElementById("kwUser").value.trim();
    var status = document.getElementById("kwStatus").value;
    if (uid) params.push("userId=" + encodeURIComponent(uid));
    if (status) params.push("status=" + encodeURIComponent(status));

    apiRequest("/api/admin/grants?" + params.join("&"))
      .then(function (r) {
        if (r.status === 403) throw new Error("没有权限：需要 role:assign");
        if (!r.ok) throw new Error("查询台账失败（HTTP " + r.status + "）");
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
      .catch(function (e) { show(e.message); });
  }

  function renderRows(list) {
    var tbody = document.getElementById("grantRows");
    tbody.innerHTML = "";
    if (!list.length) {
      tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;color:#999;">没有数据</td></tr>';
      return;
    }

    list.forEach(function (g) {
      var tr = document.createElement("tr");
      var action = g.status === "active"
        ? '<button class="row-btn danger" data-revoke="' + g.grantId + '">撤销</button>'
        : '<span style="color:#999;">—</span>';
      tr.innerHTML =
        "<td>" + g.grantId + "</td>" +
        "<td>" + (g.realName || "") + "（" + g.userId + "）</td>" +
        "<td>" + (g.roleName || g.roleId) + "</td>" +
        "<td>" + (g.grantedByName || g.grantedBy) + "</td>" +
        "<td>" + (g.startTime || "") + "</td>" +
        "<td>" + (g.endTime || "永久") + "</td>" +
        "<td>" + statusText(g.status) + "</td>" +
        "<td>" + (g.remark || "") + "</td>" +
        "<td>" + action + "</td>";
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll("button[data-revoke]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-revoke");
        if (!confirm("确定撤销授权 " + id + " 吗？用户角色将回退为原角色。")) return;
        apiRequest("/api/admin/grants/" + id + "/revoke", { method: "PUT" })
          .then(function (r) {
            return r.json().catch(function () { return null; }).then(function (d) {
              if (!r.ok) throw new Error((d && d.detail) || ("撤销失败（HTTP " + r.status + "）"));
              show("已撤销授权 " + id);
              loadGrants();
            });
          })
          .catch(function (e) { show(e.message); });
      });
    });
  }

  document.getElementById("grantBtn").addEventListener("click", function () {
    var uid = document.getElementById("grantUserId").value.trim();
    var rid = document.getElementById("grantRoleId").value;
    var endTime = document.getElementById("grantEndTime").value.trim();
    var remark = document.getElementById("grantRemark").value.trim();
    if (!uid || !rid) {
      show("请填写被授权用户ID并选择角色");
      return;
    }
    var url = "/api/admin/grants?userId=" + encodeURIComponent(uid) + "&roleId=" + encodeURIComponent(rid);
    if (endTime) url += "&endTime=" + encodeURIComponent(endTime);
    if (remark) url += "&remark=" + encodeURIComponent(remark);

    apiRequest(url, { method: "POST" })
      .then(function (r) {
        return r.json().catch(function () { return null; }).then(function (d) {
          if (!r.ok) throw new Error((d && d.detail) || ("授权失败（HTTP " + r.status + "）"));
          show("授权成功：用户 " + uid + " 已获得角色（原角色 " + d.originalRoleId + "）");
          loadGrants();
        });
      })
      .catch(function (e) { show(e.message); });
  });

  document.getElementById("searchBtn").addEventListener("click", function () { page = 1; loadGrants(); });
  document.getElementById("resetBtn").addEventListener("click", function () {
    document.getElementById("kwUser").value = "";
    document.getElementById("kwStatus").value = "";
    page = 1;
    loadGrants();
  });
  document.getElementById("prevBtn").addEventListener("click", function () { if (page > 1) { page--; loadGrants(); } });
  document.getElementById("nextBtn").addEventListener("click", function () { if (page < totalPages) { page++; loadGrants(); } });
})();