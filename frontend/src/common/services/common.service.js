import api from "../../common/tools/axios";
import { ITEMS_PER_PAGE as pageSize } from '../../settings';

const getCookies = () => {
  return api.get("/cookie/list/", {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

const deleteEntity = (app, entity, id) => {
  return api.post(`/${app}/${entity}/delete`, {
    id: id
  },
  { 
    headers: {
      'content-type': 'application/json'
    }
  }).then( (response) => {
    if (response.data) return response.data;
    else return response;
  }).catch( (error) => {
    if (error.response.status === 422) {
      return error.response.data;
    } 
  });
}; 

const saveEntity = (app, entity, data, queryParams = {}) => {
  const qs = Object.keys(queryParams).length > 0
    ? '?' + new URLSearchParams(queryParams).toString()
    : '';
  var url = `/${app}/${entity}/create${qs}`;
  if (data.id) {
    url = `/${app}/${entity}/update${qs}`;
  }

  return api.post(url, data).then((response) => {
    if (response.data) return response.data;
    else return response;
  }).catch((error) => {
    // axios.js interceptor returns err.response for HTTP errors,
    // so this catch only fires for genuine network errors.
    // Return a normalised error payload so callers always get an object.
    return { detail: [{ error: ['network-error'] }] };
  });
};  
 
const getEntities = (app, entity, status=null, searchTerm="", page = 1, extraParams={}, customPageSize) => {
  // Use provided page size or default to global
  const entityPageSize = customPageSize || pageSize;
  
  const extra = Object.keys(extraParams).length > 0
    ? '&' + Object.entries(extraParams).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&')
    : '';
  var url = `/${app}/${entity}/list?limit=${entityPageSize}&offset=${(page - 1) * entityPageSize}` +
      (searchTerm !== "" ? `&search=${encodeURIComponent(searchTerm)}` : "") + extra;
  if (status) {
    url = `/${app}/${entity}/${status}/list?limit=${entityPageSize}&offset=${(page - 1) * entityPageSize}` +
      (searchTerm !== "" ? `&search=${encodeURIComponent(searchTerm)}` : "") + extra;
  }
  return api.get(url, {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

const getEntity = (app, entity, id) => {
  return api.get(`/${app}/${entity}/${id}` , {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};


const CommonService = {
  getCookies,
  deleteEntity,
  saveEntity,
  getEntities,
  getEntity   
}

export default CommonService;