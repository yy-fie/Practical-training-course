(function () {
  // ===== 未登录不允许访问 =====
  var sessionUser = null;
  try {
    sessionUser = JSON.parse(sessionStorage.getItem("loginUser") || "null");
  } catch (e) {
    sessionUser = null;
  }

  if (!sessionUser || !sessionUser.userId) {
    var loginUrl = "login.html";
    if (window.top && window.top !== window) {
      window.top.location.href = loginUrl;
    } else {
      window.location.href = loginUrl;
    }
    return;
  }

  var userId = sessionUser.userId;
  var original = {}; // 保存原始数据，用于找出改动字段
  var fields = ["realName", "phone", "gender", "nativePlace", "politicalStatus", "email", "idCard"];

  function show(text, ok) {
    var el = document.getElementById("msg");
    el.textContent = text;
    el.style.color = ok ? "#2e7d32" : "#d93025";
  }

  function fillForm(data) {
    fields.forEach(function (f) {
      var el = document.getElementById(f);
      if (!el) return;
      el.value = data[f] == null ? "" : data[f];
      original[f] = el.value;
    });
  }

  // 打开页面时先读取最新的个人信息
  apiRequest("/api/users/" + userId)
    .then(function (r) {
      if (!r.ok) throw new Error("加载个人信息失败（HTTP " + r.status + "）");
      return r.json();
    })
    .then(fillForm)
    .catch(function (err) {
      show(err.message || "加载个人信息失败");
    });

  document.getElementById("profileForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    var current = {};
    fields.forEach(function (f) {
      current[f] = document.getElementById(f).value.trim();
    });

    // 基础校验
    if (!current.realName) {
      show("真实姓名不能为空");
      return;
    }
    if (current.phone && !/^1\d{10}$/.test(current.phone)) {
      show("手机号格式不正确（应为 11 位数字）");
      return;
    }
    if (current.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(current.email)) {
      show("邮箱格式不正确");
      return;
    }
    if (current.idCard && !/^\d{17}[\dXx]$/.test(current.idCard)) {
      show("身份证号格式不正确（18 位）");
      return;
    }

    // 只提交发生变化的字段
    var payload = {};
    fields.forEach(function (f) {
      if (current[f] !== original[f]) {
        payload[f] = current[f];
      }
    });

    if (Object.keys(payload).length === 0) {
      show("没有需要修改的内容");
      return;
    }

    var btn = document.getElementById("saveBtn");
    btn.disabled = true;
    btn.textContent = "保存中...";

    try {
      var resp = await apiRequest("/api/users/" + userId, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      var data = await resp.json().catch(function () {
        return null;
      });

      if (!resp.ok) {
        throw { message: data && data.detail ? data.detail : "保存失败（HTTP " + resp.status + "）" };
      }

      // 同步 Session，保证首页左下角显示最新姓名
      sessionStorage.setItem("loginUser", JSON.stringify(data));
      fillForm(data);
      show("保存成功", true);
    } catch (err) {
      show((err && err.message) || "保存失败");
    } finally {
      btn.disabled = false;
      btn.textContent = "保存修改";
    }
  });
})();
