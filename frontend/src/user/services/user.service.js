import api from "../../common/tools/axios";
import qs from 'qs';
import moment from 'moment';

const login = (data) => {
  return api.post("/user/login", qs.stringify({
    email: data.email,
    password: data.password
  }),
  {    
    headers: {
      'content-type': 'application/x-www-form-urlencoded'
    }
  }).then((response) => {
    return response.data;
  }).catch((error) => {
    return error.response.data;
  });
};

const logout = () => {
  return api.get("/user/logout", {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

const register = (data) => {

  let url = "/user/register";

  let payload = {
    first_name: data.first_name,
    last_name: data.last_name,                
    email: data.email,
    password: data.password,
    confPassword: data.confPassword,
    language: data.language,
    city: data.city,
    zipcode: data.zipcode,
    birthdate: moment(data.birthdate).format('YYYY-MM-DD'),
    professional: data.professional,
    company: data.company ? data.company : null,
    address: data.address ? data.address : null,
    taxnumber: data.taxnumber ? data.taxnumber : null,      
    country: data.country ? data.country : null,
    cgu: data.cgu
  }

  if (data.uidb64 && data.token) {
    payload['uidb64'] = data.uidb64;
    payload['token'] = data.token;
    url = "user/invitation"
  }

  return api.post(url, qs.stringify(payload), 
  { 
    headers: {
      'content-type': 'application/x-www-form-urlencoded'
    }
  }).then( (response) => {
    if (response.data) return response.data;
    else return response;
  }).catch( (error) => {   
    if (error.response.status === 422) {
      return error.response.data;
    } else {
        return error;
    }    
  });
};
  
const activate = (uidb64, token) => {
  return api.post("/user/activate", qs.stringify({
    uidb64: uidb64,
    token: token          
  }), 
  { 
    headers: {
      'content-type': 'application/x-www-form-urlencoded'
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
  
const reset = (data) => {
  return api.post('/user/reset_password', qs.stringify({
    email: data.email,
  }), 
  { 
    headers: {
      'content-type': 'application/x-www-form-urlencoded'
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
  
const password = (user, uidb64, token, data) => {
  let url = user ? '/user/connected_change_password' : '/user/change_password';
  return api.post(url, qs.stringify({
    uidb64: uidb64,
    token: token,   
    password: data.password,
    confPassword: data.confPassword,
    oldPassword: data.oldPassword ? data.oldPassword : null
  }), 
  { 
    headers: {
      'content-type': 'application/x-www-form-urlencoded'
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
  
const updateProfile = (data) => {
  return api.post("/user/update", qs.stringify({
    first_name: data.first_name,
    last_name: data.last_name,
    birthdate: moment(data.birthdate).format('YYYY-MM-DD'),                
    address: data.address,
    zipcode: data.zipcode,
    city: data.city,
    language: data.language,
    country: data.country, 
    professional: data.professional,
    company: data.company ? data.company : null,
    taxnumber: data.taxnumber ? data.taxnumber : null 
  }), 
  { 
    headers: {
      'content-type': 'application/x-www-form-urlencoded'
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
  
const deleteProfile = () => {
  return api.post("/user/delete", {}, 
  { 
    headers: {
      'content-type': 'application/x-www-form-urlencoded'
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

const getProfile = () => {
  return api.get("/user/getprofile", {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};
const getProfileWithToken = (uidb64, token) => {
  return api.get("/user/getprofile/" + uidb64 + "/" + token , {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};


const refreshUser = () => {
  return getProfile().then(
    (response) => {
      localStorage.setItem("user", JSON.stringify(response));
      return { user: response };
    },
    (error) => {
      localStorage.setItem("user", false);
      return { user: null };
    }     
  );
};

const userExists = (email) => {
  return api.get("/user/userexists/" + email, {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

const createUser = (data) => {
  return api.post("/user/create", qs.stringify({
    email: data.email,
    first_name: data.first_name,
    last_name: data.last_name,                
    language: data.language,
    country: data.language
  }), 
  { 
    headers: {
      'content-type': 'application/x-www-form-urlencoded'
    }
  }).then( (response) => {
    if (response.data) return response.data;
    else return response;
  }).catch( (error) => {   
    if (error.response.status === 422) {
      return error.response.data;
    } else {
        return error;
    }    
  });
};

const UserService = {
  login,
  logout,
  register,
  activate,
  reset,
  password,
  getProfile,
  getProfileWithToken,
  deleteProfile,
  updateProfile,
  refreshUser,
  userExists,
  createUser
}
  
export default UserService;
