import http from 'k6/http';
import { check } from 'k6';

export let options = {
  vus: 10,
  duration: '10s'
};

export default function () {
  const res = http.get(`${__ENV.BASE_URL}/ping`);
  check(res, { 'status is 200': (r) => r.status === 200 });
}
