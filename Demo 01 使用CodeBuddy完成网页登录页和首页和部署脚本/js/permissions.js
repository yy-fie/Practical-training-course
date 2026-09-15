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

  var me = null;
  var roleName = {};

  apiRequest("/api/me/permissions")
    .then(function (r) {
      if (!r.ok) throw new Error("登录信息失效，请重新登录");
      return r.json();
    })
    .then(function (data) {
      me = data;
      if ((data.permissions || []).indexOf("permission:manage") === -1) {
        alert("只有超级管理员可以维护权限。");
        go("home.html");
        throw new Error("no-permission");
      }
      document.getElementById("roleInfo").textContent = data.realName || "";
      loadMatrix();
    })
    .catch(function (e) {
      if (e.message !== "no-permission") show(e.message);
    });

  function loadMatrix() {
    apiRequest("/api/admin/roles/permissions")
      .then(function (r) {
        if (!r.ok) throw new Error("加载权限矩阵失败（HTTP " + r.status + "）");
        return r.json();
      })
      .then(renderMatrix)
      .catch(function (e) {
        show(e.message);
      });
  }

  function renderMatrix(data) {
    roleName = {};
    data.roles.forEach(function (r) {
      roleName[r.roleId] = r.roleName;
    });

    var mapping = data.mapping || {};
    var tbody = document.getElementById("permRows");
    tbody.innerHTML = "";

    data.roles.forEach(function (role) {
      var assigned = mapping[String(role.roleId)] || [];
      var boxes = data.permissions
        .map(function (p) {
          var checked = assigned.indexOf(p.permId) !== -1 ? " checked" : "";
          return (
            '<label class="perm-item"><input type="checkbox" value="' +
            p.permCode + '"' + checked + "> " + p.permName + "</label>"
          );
        })
        .join("");

      var tr = document.createElement("tr");
      tr.innerHTML =
        "<td>" + role.roleName + "</td>" +
        "<td>" + (role.parentRoleId ? (roleName[role.parentRoleId] || role.parentRoleId) : "—") + "</td>" +
        '<td class="perm-cell">' + boxes + "</td>" +
        '<td><button class="row-btn" data-save="' + role.roleId + '">保存</button></td>';
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll("button[data-save]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var roleId = btn.getAttribute("data-save");
        var row = btn.closest("tr");
        var codes = Array.prototype.slice
          .call(row.querySelectorAll("input[type=checkbox]:checked"))
          .map(function (c) {
            return c.value;
          });

        apiRequest("/api/admin/roles/" + roleId + "/permissions", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ permCodes: codes })
        })
          .then(function (r) {
            return r
              .json()
              .catch(function () {
                return null;
              })
              .then(function (d) {
                if (!r.ok) throw new Error((d && d.detail) || "保存失败（HTTP " + r.status + "）");
                show("角色「" + roleName[roleId] + "」权限已保存（" + codes.length + " 项）");
              });
          })
          .catch(function (e) {
            show(e.message);
          });
      });
    });
  }
})();