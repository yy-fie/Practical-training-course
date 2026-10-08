const api = require('../../utils/api');
Page({
  data: { station: null, months: [], count: 0, amount: '0.00', loading: false, error: '' },
  onLoad(options) { this.stationId = Number(options.id); },
  onShow() { this.load(); },
  async load() {
    if (!api.requireSession() || this.data.loading) return;
    if (!Number.isInteger(this.stationId) || this.stationId < 1) { this.setData({ error: '站点编号不正确' }); return; }
    this.setData({ loading: true, error: '' });
    try {
      const station = await api.request('/api/stations/' + this.stationId);
      this.setData({ station });
      const result = await api.request('/api/stations/trip-stats' + api.query({ station_name: station.station_name }));
      const max = Math.max(1, ...(result.data || []).map(item => Number(item['乘车次数']) || 0));
      let count = 0, amount = 0;
      const months = (result.data || []).map(item => {
        const trips = Number(item['乘车次数']) || 0;
        const income = Number(item['总金额']) || 0;
        count += trips; amount += income;
        return { month: item['乘车月份'], count: trips, amount: income.toFixed(2), percent: Math.round(trips / max * 100) };
      });
      this.setData({ months, count, amount: amount.toFixed(2) });
    } catch (error) { this.setData({ error: error.message, months: [], count: 0, amount: '0.00' }); }
    finally { this.setData({ loading: false }); }
  }
});
