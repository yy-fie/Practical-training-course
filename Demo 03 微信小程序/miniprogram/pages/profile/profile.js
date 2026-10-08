const api = require('../../utils/api');
const fields = ['realName', 'phone', 'email', 'gender', 'nativePlace', 'politicalStatus', 'idCard'];
Page({
  data: { user: {}, form: {}, loading: false, saving: false, exiting: false, canEdit: false, canChangePassword: false, error: '' },
  onShow() { this.load(); },
  async load() {
    if (!api.requireSession() || this.data.loading) return;
    this.setData({ loading: true, error: '' });
    try {
      const me = await api.permissions();
      const user = await api.request('/api/users/' + api.session().user.userId);
      const form = {};
      fields.forEach(field => { form[field] = user[field] || ''; });
      this.original = Object.assign({}, form);
      api.updateUser(user);
      this.setData({ user, form, canEdit: me.permissions.indexOf('profile:self') !== -1,
        canChangePassword: me.permissions.indexOf('password:self') !== -1 });
    } catch (error) { this.setData({ error: error.message, canEdit: false, canChangePassword: false }); }
    finally { this.setData({ loading: false }); }
  },
  onInput(event) { this.setData({ ['form.' + event.currentTarget.dataset.field]: event.detail.value, error: '' }); },
  async save() {
    if (!this.data.canEdit || this.data.saving || this.data.loading) return;
    const form = {};
    fields.forEach(field => { form[field] = (this.data.form[field] || '').trim(); });
    if (!form.realName) { this.setData({ error: '真实姓名不能为空' }); return; }
    if (form.phone && !/^1\d{10}$/.test(form.phone)) { this.setData({ error: '手机号应为 11 位数字' }); return; }
    if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) { this.setData({ error: '邮箱格式不正确' }); return; }
    if (form.idCard && !/^\d{17}[\dXx]$/.test(form.idCard)) { this.setData({ error: '身份证号应为 18 位' }); return; }
    const payload = {};
    fields.forEach(field => { if (form[field] !== this.original[field]) payload[field] = form[field]; });
    if (!Object.keys(payload).length) { wx.showToast({ title: '没有需要保存的修改', icon: 'none' }); return; }
    this.setData({ saving: true, error: '' });
    try {
      const user = await api.request('/api/users/' + api.session().user.userId, { method: 'PUT', data: payload });
      api.updateUser(user);
      this.original = Object.assign({}, form);
      this.setData({ user, form });
      wx.showToast({ title: '资料已保存', icon: 'success' });
    } catch (error) { this.setData({ error: error.message }); }
    finally { this.setData({ saving: false }); }
  },
  password() { wx.navigateTo({ url: '/pages/password/password' }); },
  async logout() {
    if (this.data.exiting) return;
    this.setData({ exiting: true, error: '' });
    try { await api.logout(); }
    catch (error) { this.setData({ error: error.message }); }
    finally { this.setData({ exiting: false }); }
  }
});
