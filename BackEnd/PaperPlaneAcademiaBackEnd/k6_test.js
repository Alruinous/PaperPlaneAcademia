import http from 'k6/http';
import { check, sleep } from 'k6';
 

// 服务地址
const serveAddress = "http://113.44.138.144:8000";
// const serveAddress = "http://localhost:8000";

// 配置设置：模拟并发用户
export let options = {
    stages: [
      { duration: '30s', target: 1000 }, // 30秒内增加到20个并发用户
      { duration: '1m', target: 1000 },  // 保持20个并发用户，1分钟
      { duration: '30s', target: 0 },  // 30秒内降到0个并发用户
    ],
  };

// 假设的有效的用户名和密码
const validUser = {
    username: 'lorian',
    password: 'lorian',
};

// 封装登录请求的函数
function loginUser(user) {
    const payload = JSON.stringify(user);
    const headers = { 'Content-Type': 'application/json' };
    return http.post(serveAddress + '/user/login/', payload, { headers: headers });
}

// 定义请求数据
const searchData = {
    searchConditions: [
        {
            logic: null,
            value: "Java",
            scope: "title",
        },
        {
            logic: "or",
            value: "Report",
            scope: "title",
        },
    ],
    dateRange: [
        null, null
    ],
    filter: {
        keys: [],
        years: [],
        authorOrganizations: [],
    },
    userId: "13",
    page: 4,
    sort: 2
};

// 封装POST请求函数
function fetchResults(data) {
    const headers = { 'Content-Type': 'application/json' };
    return http.post(serveAddress + '/papers/search/', JSON.stringify(data), { headers: headers });
}


// 主函数
export default function () {
    //登录
    // let validResponse = loginUser(validUser);
    // check(validResponse, {
    //   'login successfully!': (r) => r.status === 200,
    // });


    //学者搜索
    let searchResponse = fetchResults(searchData);
    check(searchResponse, {
        'author search successfully!': (r) => r.status === 200,
    });
 
    sleep(1);
}