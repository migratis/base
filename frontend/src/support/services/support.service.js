import api from "../../common/tools/axios";
import qs from 'qs';

const sendSupport = (data) => {
    return api.post("/support/offline", qs.stringify({
      contact: data.email,
      topic_id: data.topic_id,                
      content: data.content,
      language: data.language,      
      object: data.object
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

const closeTicket = (id) => {
  return api.get("/support/ticket/close/" + id,   {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }).catch( (error) => {
      if (error.response.status === 422) {
        return error.response.data;
      } 
    });
};  

const saveTicket = (data) => {
  var url = "/support/ticket/create";
  if (data.id) {
    url = "/support/ticket/update/" + data.id;
  } 
  return api.post(url, qs.stringify({
    topic_id: data.topic_id,                
    content: data.content,
    language: data.language,
    object: data.object
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
 
const getTopics = () => {
  return api.get("/support/topics", {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

const getTickets = () => {
  return api.get("/support/ticket/list" , {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

const getFullTickets = () => {
  return api.get("/support/tickets" , {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

const getTicket = (id) => {
  return api.get("/support/ticket/" + id, {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

const saveThread = (data, ticketId) => {
  if (!data.id) {
    var url = "/support/" + ticketId + "/thread/create";
  } else {
    url = "/support/thread/update/" + data.id;
  }
  return api.post(url, qs.stringify({
    content: data.content,
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

const getThread = (id) => {
  return api.get("/support/thread/" + id, {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

async function uploadFile(id, data) {
  return api.post("/support/" + id + "/upload", data,
    { 
      headers: {
        'content-type': 'multipart/form-data'
      }
    }
  ).then( response => {
    if (response.data) return response.data;
    else return response;
  }).catch( error => {
    if(error.response) {
      if(error.response.data) {
        return error.response.data;          
      } else {
        return error.response;
      }
    }
  });
}; 

const download = (file) => {
  return api.get("/support/download/" + file.id, {})
    .then( (response) => {
      if (response.data) return response.data;
      else return response;
    }
  );
};

const SupportService = {
  sendSupport,
  closeTicket,    
  saveTicket,
  getTickets,
  getFullTickets,  
  getTicket,
  getThread,    
  getTopics,
  saveThread,
  uploadFile,
  download,
}
  
export default SupportService;