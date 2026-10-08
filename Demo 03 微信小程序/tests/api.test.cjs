const assert = require('node:assert/strict');
const path = require('node:path');
const source = path.resolve(__dirname, '../miniprogram/utils/api.js');
let storage, calls, navigations, handler, api;
function setup() {
  storage = new Map(); calls = []; navigations = []; handler = null;
  global.getApp = () => ({globalData:{permissions:[]}});
  global.wx = {
    getStorageSync: key => storage.get(key),
    setStorageSync: (key,value) => storage.set(key,value),
    removeStorageSync: key => storage.delete(key),
    reLaunch: options => {navigations.push(options.url); if(options.complete)options.complete();},
    request: options => {calls.push(options); handler(options);}
  };
  delete require.cache[source]; api = require(source);
}
function seed() { storage.set('metro.session',{user:{userId:1,realName:'测试'},accessToken:'old-access',refreshToken:'old-refresh'}); }
function success(request,status,data={}) { request.success({statusCode:status,data}); }
async function run(name,fn) { setup(); await fn(); console.log('PASS '+name); }
(async()=>{
  await run('login uses JSON credentials and stores session',async()=>{
    handler = request => success(request,200,{user:{userId:1},accessToken:'access',refreshToken:'refresh'});
    await api.login('test@example.com','123456');
    assert.equal(calls[0].method,'POST'); assert.equal(calls[0].url,'http://127.0.0.1:9001/api/auth/login');
    assert.deepEqual(calls[0].data,{username:'test@example.com',password:'123456'});
    assert.equal(api.session().accessToken,'access');
  });
  await run('concurrent expired requests share one refresh and retry with Bearer',async()=>{
    seed(); let refreshes=0;
    handler = request => {
      if(request.url.endsWith('/api/auth/refresh')){
        refreshes++; setTimeout(()=>success(request,200,{accessToken:'new-access',refreshToken:'new-refresh'}),20);
      }else if(request.header.Authorization==='Bearer old-access') success(request,401);
      else success(request,200,{ok:true});
    };
    const result=await Promise.all([api.request('/api/me/permissions'),api.request('/api/stations')]);
    assert.deepEqual(result,[{ok:true},{ok:true}]); assert.equal(refreshes,1);
    assert.equal(api.session().refreshToken,'new-refresh');
    assert(calls.every(call=>!call.header['X-User-Id']));
  });
  await run('forbidden request preserves session and displays server message',async()=>{
    seed(); handler=request=>success(request,403,{detail:'没有业务权限'});
    await assert.rejects(api.request('/api/stations'),/没有业务权限/);
    assert.equal(calls.length,1); assert(api.session()); assert.equal(navigations.length,0);
  });
  await run('invalid refresh clears session and redirects',async()=>{
    seed(); handler=request=>success(request,401);
    await assert.rejects(api.request('/api/stations'));
    assert.equal(api.session(),null); assert.deepEqual(navigations,['/pages/login/login']);
  });
  await run('temporary refresh failure preserves login',async()=>{
    seed(); handler=request=>success(request,request.url.endsWith('/api/auth/refresh')?503:401);
    await assert.rejects(api.request('/api/stations'),/暂时不可用/);
    assert(api.session()); assert.equal(navigations.length,0);
  });
  await run('network failure preserves login',async()=>{
    seed(); handler=request=>request.fail({errMsg:'timeout'});
    await assert.rejects(api.request('/api/stations'),/无法连接/);
    assert(api.session());
  });
  await run('clear during refresh cannot restore stale session',async()=>{
    seed(); let finish;
    handler=request=>{
      if(request.url.endsWith('/api/auth/refresh'))finish=()=>success(request,200,{accessToken:'new',refreshToken:'new'});
      else success(request,401);
    };
    const pending=api.request('/api/stations');
    await new Promise(resolve=>setImmediate(resolve));
    api.clearSession(); finish();
    await assert.rejects(pending,/登录状态已变化/); assert.equal(api.session(),null);
  });
  await run('old refresh cannot erase a newly logged-in account',async()=>{
    seed(); let finish;
    handler=request=>{
      if(request.url.endsWith('/api/auth/refresh'))finish=()=>success(request,200,{accessToken:'stale',refreshToken:'stale'});
      else if(request.url.endsWith('/api/auth/login'))success(request,200,{user:{userId:2},accessToken:'second',refreshToken:'second-refresh'});
      else success(request,401);
    };
    const pending=api.request('/api/stations');
    await new Promise(resolve=>setImmediate(resolve));
    await api.login('second','123456'); finish();
    await assert.rejects(pending,/登录状态已变化/); assert.equal(api.session().user.userId,2);
    assert.equal(navigations.length,0);
  });
  await run('logout revokes server session before clearing local state',async()=>{
    seed(); handler=request=>{
      assert(api.session()); assert(request.url.endsWith('/api/auth/logout'));
      assert.equal(request.header.Authorization,'Bearer old-access'); success(request,200);
    };
    await api.logout(); assert.equal(api.session(),null); assert.equal(navigations[0],'/pages/login/login');
  });
  await run('query strings preserve Chinese and omit empty filters',async()=>{
    assert.equal(api.query({station_name:'人民广场',line:'',page:1}),'?station_name='+encodeURIComponent('人民广场')+'&page=1');
  });
})().catch(error=>{console.error(error);process.exitCode=1;});
