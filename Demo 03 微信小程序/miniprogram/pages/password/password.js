const api = require('../../utils/api');
Page({
  data: { oldPassword: '', newPassword: '', confirmPassword: '', allowed: false, loading: false, submitting: false, error: '' },
  async onShow() {
    if (!api.requireSession()) return;
    this.setData({ loading: true, error: '' });
    try { await api.permissions(); this.setData({ allowed: api.hasPermission('password:self') }); }
    catch (error) { this.setData({ error: error.message, allowed: false }); }
    finally { this.setData({ loading: false }); }
  },
  onInput(event) { this.setData({ [event.currentTarget.dataset.field]: event.detail.value, error: '' }); },
  async submit() {
    if (this.data.submitting || !this.data.allowed) return;
    const { oldPassword, newPassword, confirmPassword } = this.data;
    if (!oldPassword || !newPassword || !confirmPassword) { this.setData({ error: '请填写原密码、新密码和确认密码' }); return; }
    if (newPassword.length < 6) { this.setData({ error: '新密码至少需要 6 位' }); return; }
    if (newPassword !== confirmPassword) { this.setData({ error: '两次输入的新密码不一致' }); return; }
    if (oldPassword === newPassword) { this.setData({ error: '新密码不能与原密码相同' }); return; }
    this.setData({ submitting: true, error: '' });
    try {
      await api.request('/api/users/' + api.session().user.userId + '/password', {
        method: 'PUT', data: { oldPassword, newPassword, confirmPassword }
      });
      api.clearSession();
      this.setData({ oldPassword: '', newPassword: '', confirmPassword: '' });
      wx.showModal({ title: '密码已修改', content: '请使用新密码重新登录。', showCancel: false,
        success: () => wx.reLaunch({ url: '/pages/login/login' }) });
    } catch (error) { this.setData({ error: error.message }); }
    finally { this.setData({ submitting: false }); }
  }
});
