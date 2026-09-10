(function () {
  var canvas = document.getElementById("captchaCanvas");
  var ctx = canvas.getContext("2d");
  var code = "";

  function rand(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function drawCode() {
    code = "";
    var chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    for (var i = 0; i < 4; i++) {
      code += chars.charAt(rand(0, chars.length - 1));
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "#f2f6ff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (var i = 0; i < 5; i++) {
      ctx.beginPath();
      ctx.strokeStyle = "rgba(84,112,198," + (0.15 + Math.random() * 0.2) + ")";
      ctx.moveTo(rand(0, canvas.width), rand(0, canvas.height));
      ctx.lineTo(rand(0, canvas.width), rand(0, canvas.height));
      ctx.stroke();
    }

    ctx.font = "bold 24px Arial";
    for (var i = 0; i < code.length; i++) {
      ctx.save();
      ctx.translate(14 + i * 20, 30);
      ctx.rotate((rand(-25, 25) * Math.PI) / 180);
      ctx.fillStyle =
        "rgb(" + rand(30, 100) + "," + rand(60, 130) + "," + rand(150, 220) + ")";
      ctx.fillText(code.charAt(i), -8, 0);
      ctx.restore();
    }
  }

  function refresh() {
    drawCode();
    document.getElementById("captchaInput").value = "";
  }

  canvas.addEventListener("click", refresh);
  document.getElementById("captchaRefresh").addEventListener("click", refresh);

  document.getElementById("loginForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    var msgEl = document.getElementById("errorMsg");
    var btn = document.getElementById("loginBtn");
    var username = document.getElementById("username").value.trim();
    var password = document.getElementById("password").value;
    var captcha = document.getElementById("captchaInput").value.trim().toUpperCase();

    msgEl.textContent = "";

    if (!username || !password) {
      msgEl.textContent = "请输入用户名和密码";
      return;
    }
    if (!captcha) {
      msgEl.textContent = "请输入验证码";
      return;
    }
    if (captcha !== code) {
      msgEl.textContent = "验证码错误，请重新输入";
      refresh();
      return;
    }

    btn.disabled = true;
    btn.textContent = "验证中...";

    try {
      var user = await apiLogin(username, password);
      // 登录成功：把用户信息写入 Session（sessionStorage），再跳转首页
      sessionStorage.setItem("loginUser", JSON.stringify(user));
      window.location.href = "home.html";
    } catch (err) {
      msgEl.textContent = (err && err.message) || "用户名或密码错误";
      refresh();
    } finally {
      btn.disabled = false;
      btn.textContent = "登 录";
    }
  });

  drawCode();
})();
