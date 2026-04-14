import axios from 'axios';
import { API_SERVER } from "../../settings";
import { trackPromise } from 'react-promise-tracker';

const customAxios = axios.create({
    baseURL: `${API_SERVER}`,
});
customAxios.defaults.xsrfCookieName = 'csrftoken'
customAxios.defaults.xsrfHeaderName = "X-CSRFToken"
customAxios.defaults.withCredentials = true;

const cookieAxios = axios.create({
  baseURL: `${API_SERVER}`,
});
cookieAxios.defaults.withCredentials = true;


customAxios.interceptors.request.use(
  async (request) => {

    if (request.url.match("/download/")) {
      request.responseType = "blob";
      return request;
    }

    if(request.method === "post") {

      if (
        request.url.match("user/login") 
        || request.url.match("/user/change_password") 
        || request.url.match("/user/reset_password")
        || request.url.match("/user/activate")
        || request.url.match("/user/register")              
      ) {
        return request;
      }

      try {
        const response = await cookieAxios.get("/csrftoken");
        const match = response.data.match(/value="([^"]+)"/);
        if (match) request.headers['X-CSRFToken'] = match[1];
        return request;     
      } catch (error) {
        console.log(error);
      }

    }

    return request;

  }, (error) => {
    return Promise.reject(error);
  }
);

customAxios.interceptors.response.use(
  (response) => {
    return response;
  },
  async (err) => {

    if (err && err.response && err.response.status === 401) {
      localStorage.setItem("user", false);
      localStorage.setItem("session_expired", "true");
      const event = new CustomEvent('session-expired', {
        detail: { url: err.config?.url }
      });
      window.dispatchEvent(event);
    }

    if (err && err.response && err.response.status === 403) {
      let user = JSON.parse(localStorage.getItem("user"));
      if (user) {
        user.subscription = null;
        localStorage.setItem("user", JSON.stringify(user));
      }
      window.location = "/subscribe";
    }
    
    if (err.response) return err.response; 
    else return err;
  
  }
);

const get = param => trackPromise(customAxios.get(param));
const post = (param, body) => trackPromise(customAxios.post(param, body));
const put = (param, body) => trackPromise(customAxios.put(param, body));
const del = param => trackPromise(customAxios.delete(param));

 const api = {
  get,
  post,
  put,
  delete: del,
};

export default api;