const api = require('../../utils/api');
Page({
  data: { station_name: '', line: '', district: '', allowed: false, loading: false, submitting: false, error: '' },
  async onShow() {
    if (!api.requireSession()) return;
    this.setData({ loading: true, error: '' });
    try { await api.permissions(); this.setData({ allowed: api.hasPermission('user:edit') }); }
    catch (error) { this.setData({ error: error.message, allowed: false }); }
    finally { this.setData({ loading: false }); }
  },
  onInput(event) { this.setData({ [event.currentTarget.dataset.field]: event.detail.value, error: '' }); },
  async submit() {
    if (this.data.submitting || !this.data.allowed) return;
    const payload = { station_name: this.data.station_name.trim(), line: this.data.line.trim(), district: this.data.district.trim() };
    if (!payload.station_name || !payload.line || !payload.district) {
      this.setData({ error: '请填写站点名称、线路和区域' }); return;
    }
    this.setData({ submitting: true, error: '' });
    try {
      const station = await api.request('/api/stations', { method: 'POST', data: payload });
      wx.showToast({ title: '站点已添加', icon: 'success' });
      if (api.hasPermission('analysis:view')) wx.redirectTo({ url: '/pages/station-detail/station-detail?id=' + station.station_id });
      else wx.switchTab({ url: '/pages/index/index' });
    } catch (error) { this.setData({ error: error.message }); }
    finally { this.setData({ submitting: false }); }
  }
});
