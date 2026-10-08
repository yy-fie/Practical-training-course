const api = require('../../utils/api');
Page({
  data: { name: '', loading: false, error: '', canView: false, canAdd: false, stationCount: '—', roleId: '' },
  onShow() { this.load(); },
  async onPullDownRefresh() { try { await this.load(); } finally { wx.stopPullDownRefresh(); } },
  async load() {
    if (!api.requireSession() || this.data.loading) return;
    this.setData({ loading: true, error: '' });
    try {
      const me = await api.permissions();
      const canView = me.permissions.indexOf('analysis:view') !== -1;
      this.setData({ name: me.realName || '用户', roleId: me.roleId, canView,
        canAdd: me.permissions.indexOf('user:edit') !== -1, stationCount: '—' });
      if (canView) {
        const result = await api.request('/api/stations?page=1&rows=1');
        this.setData({ stationCount: result.total });
      }
    } catch (error) { this.setData({ error: error.message, canView: false, canAdd: false }); }
    finally { this.setData({ loading: false }); }
  },
  openStations() { wx.switchTab({ url: '/pages/stations/stations' }); },
  openCreate() { wx.navigateTo({ url: '/pages/station-create/station-create' }); },
  openProfile() { wx.switchTab({ url: '/pages/profile/profile' }); }
});
