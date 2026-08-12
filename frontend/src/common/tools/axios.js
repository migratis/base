import axios from 'axios';
import { toast } from 'react-toastify';
import { API_SERVER } from "../../settings";
import { trackPromise } from 'react-promise-tracker';
import i18n from '../../i18n';

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

// Endpoints that report their own refusals where the user is looking, so the
// generic toast would name the wrong thing on top of a message that is already
// right. `routing/snap` is refused per *caller*, not per record: the editor
// keeps the traced line and badges it "not a road route", and "access denied"
// beside that suggests the user was barred from their own record. The status is
// still returned to the caller untouched — this silences the toast, not the
// outcome.
const SILENT_403 = [/routing\/snap$/];

const silent403 = (err) => {
  const url = (err && (err.config?.url || err.response?.config?.url)) || '';
  return SILENT_403.some((pattern) => pattern.test(url));
};

customAxios.interceptors.response.use(
  (response) => {
    return response;
  },
  async (err) => {

    if (err && err.response && err.response.status === 401) {
      // Only a session that existed can expire. A 401 on an anonymous visit
      // means "not logged in", which is a perfectly legal state on a public
      // page — flagging it there left the flag in localStorage and prompted for
      // a login on the next page, whichever page that was.
      const storedUser = localStorage.getItem("user");
      const hadSession = storedUser && storedUser !== 'false';

      localStorage.setItem("user", false);

      if (hadSession) {
        localStorage.setItem("session_expired", "true");
        const event = new CustomEvent('session-expired', {
          detail: { url: err.config?.url }
        });
        window.dispatchEvent(event);
      }
    }

    if (err && err.response && err.response.status === 403 && !silent403(err)) {
      toast.error(i18n.t('access-denied'));
    }
    
    if (err.response) return err.response; 
    else return err;
  
  }
);

// The third argument is axios' per-request config, and it is forwarded rather
// than dropped: a caller that adds a header here — `routing.service` adds the
// sandbox token — otherwise sends a request without it and reads the refusal as
// the service being down.
const get = (param, config) => trackPromise(customAxios.get(param, config));
const post = (param, body, config) => trackPromise(customAxios.post(param, body, config));
const put = (param, body, config) => trackPromise(customAxios.put(param, body, config));
const del = (param, config) => trackPromise(customAxios.delete(param, config));

 const api = {
  get,
  post,
  put,
  delete: del,
};

export default api;