const api = require('../../utils/api');
Page({
  data: { username: '', password: '', submitting: false, error: '' },
  onShow() { if (api.session()) wx.switchTab({ url: '/pages/index/index' }); },
  onInput(event) { this.setData({ [event.currentTarget.dataset.field]: event.detail.value, error: '' }); },
  async submit() {
    if (this.data.submitting) return;
    const username = this.data.username.trim();
    if (!username || !this.data.password) { this.setData({ error: '请填写手机号或邮箱及密码' }); return; }
    this.setData({ submitting: true, error: '' });
    try {
      await api.login(username, this.data.password);
      this.setData({ password: '' });
      wx.switchTab({ url: '/pages/index/index' });
    } catch (error) { this.setData({ error: error.message }); }
    finally { this.setData({ submitting: false }); }
  }
});
