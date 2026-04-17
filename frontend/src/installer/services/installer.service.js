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

const listInstalled = () =>
  api.get("/installer/installed").then((r) => r.data);

const uninstall = (module) =>
  api.post(`/installer/uninstall/${encodeURIComponent(module)}`).then((r) => r.data);

const InstallerService = {
  getSession,
  connect,
  disconnect,
  listApps,
  install,
  frontendZipUrl,
  listInstalled,
  uninstall,
};

export default InstallerService;
