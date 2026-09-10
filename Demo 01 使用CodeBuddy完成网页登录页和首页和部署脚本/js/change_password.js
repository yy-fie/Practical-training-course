(function () {
  // ===== 未登录不允许访问：直接输入网址也会被拦截回登录页 =====
  var user = null;
  try {
    user = JSON.parse(sessionStorage.getItem("loginUser") || "null");
  } catch (e) {
    user = null;
  }

  if (!user || !user.userId) {
    var loginUrl = "login.html";
    if (window.top && window.top !== window) {
      window.top.location.href = loginUrl; // 在 iframe 中打开时，跳转整个页面
    } else {
      window.location.href = loginUrl;
    }
    return;
  }

  document.getElementById("curUser").textContent =
    user.realName || user.phone || "userId=" + user.userId;

  function show(text, ok) {
    var el = document.getElementById("msg");
    el.textContent = text;
    el.style.color = ok ? "#2e7d32" : "#d93025";
  }

  document.getElementById("pwdForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    var oldPwd = document.getElementById("oldPassword").value;
    var newPwd = document.getElementById("newPassword").value;
    var confirmPwd = document.getElementById("confirmPassword").value;
    var btn = document.getElementById("submitBtn");

    // 前端基础校验（与后端校验保持一致）
    if (!oldPwd || !newPwd || !confirmPwd) {
      show("原始密码、新密码、确认密码都不能为空");
      return;
    }
    if (newPwd !== confirmPwd) {
      show("两次输入的新密码不一致");
      return;
    }
    if (newPwd === oldPwd) {
      show("新密码不能与原始密码相同");
      return;
    }
    if (newPwd.length < 6) {
      show("新密码长度不能少于 6 位");
      return;
    }

    btn.disabled = true;
    btn.textContent = "提交中...";

    try {
      var resp = await fetch(API_BASE + "/api/users/" + user.userId + "/password", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          oldPassword: oldPwd,
          newPassword: newPwd,
          confirmPassword: confirmPwd
        })
      });
      var data = await resp.json().catch(function () {
        return null;
      });

      if (!resp.ok) {
        throw {
          message: data && data.detail ? data.detail : "修改失败（HTTP " + resp.status + "）"
        };
      }

      show("密码修改成功，请使用新密码重新登录...", true);
      sessionStorage.removeItem("loginUser");

      setTimeout(function () {
        if (window.top && window.top !== window) {
          window.top.location.href = "login.html";
        } else {
          window.location.href = "login.html";
        }
      }, 1500);
    } catch (err) {
      show((err && err.message) || "修改失败");
    } finally {
      btn.disabled = false;
      btn.textContent = "确认修改";
    }
  });
})();
