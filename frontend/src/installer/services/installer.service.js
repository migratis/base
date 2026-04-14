import api from "../../common/tools/axios";

const getSession = () =>
  api.get("/installer/session").then((r) => r.data);

const connect = (email, password, url) =>
  api.post("/installer/connect", { email, password, url }).then((r) => r.data);

const disconnect = () =>
  api.delete("/installer/connect").then((r) => r.data);

const listApps = () =>
  api.get("/installer/apps").then((r) => r.data);

const install = (appId) =>
  api.post(`/installer/install/${appId}`).then((r) => r.data);

const frontendZipUrl = (appId) =>
  `/backend/api/installer/frontend-zip/${appId}`;

const InstallerService = {
  getSession,
  connect,
  disconnect,
  listApps,
  install,
  frontendZipUrl,
};

export default InstallerService;
