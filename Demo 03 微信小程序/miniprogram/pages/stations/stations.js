const api = require('../../utils/api');
Page({
  data: { keyword: '', lines: ['全部线路'], districts: ['全部区域'], lineIndex: 0, districtIndex: 0,
    items: [], page: 0, total: 0, loading: false, error: '', canView: false, canAdd: false, hasMore: false },
  onShow() { this.load(); },
  async onPullDownRefresh() { try { await this.load(); } finally { wx.stopPullDownRefresh(); } },
  onReachBottom() { if (this.data.hasMore && !this.data.loading) this.fetchPage(false); },
  onInput(event) { this.setData({ keyword: event.detail.value }); },
  search() { return this.fetchPage(true); },
  filter(event) {
    this.setData({ [event.currentTarget.dataset.field]: Number(event.detail.value) });
    this.fetchPage(true);
  },
  async load() {
    if (!api.requireSession()) return;
    this.setData({ loading: true, error: '' });
    try {
      const me = await api.permissions();
      const canView = me.permissions.indexOf('analysis:view') !== -1;
      this.setData({ canView, canAdd: me.permissions.indexOf('user:edit') !== -1 });
      if (!canView) { this.setData({ items: [], total: 0, hasMore: false }); return; }
      const filters = await Promise.all([api.request('/api/stations/lines'), api.request('/api/stations/districts')]);
      const previousLine = this.data.lines[this.data.lineIndex];
      const previousDistrict = this.data.districts[this.data.districtIndex];
      const lines = ['全部线路'].concat((filters[0].lines || []).filter(Boolean));
      const districts = ['全部区域'].concat((filters[1].districts || []).filter(Boolean));
      this.setData({ lines, districts, lineIndex: Math.max(0, lines.indexOf(previousLine)),
        districtIndex: Math.max(0, districts.indexOf(previousDistrict)) });
      await this.fetchPage(true);
    } catch (error) { this.setData({ error: error.message, items: [], hasMore: false }); }
    finally { this.setData({ loading: false }); }
  },
  async fetchPage(reset) {
    if (!this.data.canView || !api.requireSession()) return;
    if (!reset && this.data.loading) return;
    const version = (this._queryVersion || 0) + 1;
    this._queryVersion = version;
    const page = reset ? 1 : this.data.page + 1;
    this.setData({ loading: true, error: '' });
    try {
      const result = await api.request('/api/stations' + api.query({ page, rows: 15,
        station_name: this.data.keyword.trim(), line: this.data.lineIndex ? this.data.lines[this.data.lineIndex] : '',
        district: this.data.districtIndex ? this.data.districts[this.data.districtIndex] : '' }));
      if (this._queryVersion !== version) return;
      const items = reset ? result.rows : this.data.items.concat(result.rows);
      this.setData({ items, total: result.total, page, hasMore: items.length < result.total });
    } catch (error) { if (this._queryVersion === version) this.setData({ error: error.message }); }
    finally { if (this._queryVersion === version) this.setData({ loading: false }); }
  },
  open(event) { wx.navigateTo({ url: '/pages/station-detail/station-detail?id=' + event.currentTarget.dataset.id }); },
  add() { wx.navigateTo({ url: '/pages/station-create/station-create' }); }
});
