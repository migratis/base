import { useState, useEffect, useMemo, useCallback } from "react";
import { useTranslation } from 'react-i18next';
import {
  IoAddCircleOutline as AddCircleOutline
} from 'react-icons/io5';
import {
  CommonModal as EditModal
} from "../modals/CommonModal";
import CommonService from '../services/common.service';
import { toast } from 'react-toastify';
import { useLocation } from 'react-router-dom';
import MigratisPagination from '../../common/components/Pagination';
import { ITEMS_PER_PAGE as pageSize } from '../../settings';
import Badge from 'react-bootstrap/Badge';
import { Tabs, Tab } from 'react-bootstrap';
import Container from 'react-bootstrap/Container';
import { COLOR_LINK } from "../../settings";

const Entities = (props) => {
  const { t } = useTranslation(props.entity);
  const [ entities, setEntities ] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [start, setStart] = useState(0);
  const [end, setEnd] = useState(0);
  const location = useLocation();
  const [ entity, setEntity ] = useState(props.newEntity);
  const [ refresh, setRefresh ] = useState(false);
  const [ editModalShow, setEditModalShow ] = useState(false);
  const [ currentTab, setCurrentTab ] = useState('active');
  const [ wait, setWait ] = useState(true);
  const [ noEntity, setNoEntity ] = useState(true);
  const [pageActive , setPageActive] = useState(1);
  const [pageInactive , setPageInactive] = useState(1);
  const [ disableSubmit, setDisableSubmit ] = useState(false);
	const [ serverErrors, setServerErrors ] = useState([]);

  // Use module-provided page size or default
  const entityPageSize = props.pageSize || pageSize;

  // Stable serialised key — prevents a new `{}` reference on every parent render
  // from re-triggering the fetch effect endlessly.
  const extraParamsKey = JSON.stringify(props.extraParams);
  const extraParams = useMemo(() => props.extraParams || {}, [extraParamsKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleEdit = (id=null) => {
    if (id) {  
      CommonService.getEntity(props.app, props.entity , id).then((response) => {
        if (Object.keys(response).length > 0) {
          setEntity(response);
        } else {
          setEntity(props.newEntity);
        }
        setEditModalShow(true);   
      });
    } else {
      setEntity(props.newEntity);
      setEditModalShow(true);
    }
  };

  const handleDelete = (id) => {
    if (window.confirm(t('confirm-delete-record'))) {
      CommonService.deleteEntity(props.app, props.entity, id).then(
        (response) => {
          if (response.detail[0].success) {
            toast.success(t(response.detail[0].success[0], {entity: t(props.entity)}));
            setRefresh(prev => !prev);
          } else {
            toast.error(t('error-occured'));
          }
        }
      );    
    }      
  };

  const handleRefresh = useCallback(() => {
    setRefresh(prev => !prev);
  }, []);

  const saveEntity = (data, relations=[]) => {
    setDisableSubmit(true);
    CommonService.saveEntity(props.app, props.entity, data, extraParams).then(
      (response) => {
        setDisableSubmit(false);
        if (!response || !response.detail || !response.detail[0]) {
          toast.error(t('error-occured'));
          return;
        }
        if (response.detail[0].success) {
          toast.success(t(response.detail[0].success[0], {entity: t(props.entity)}));
          if (response.ai_triggered) {
            toast.info(t('ai-building-model', { ns: props.entity }), { autoClose: 8000 });
          }
          closeAndUpdateEditModal(data);
        } else {
          var message = {};          
          if (response.detail[0] && response.detail[0].loc) {
            for (var i=0;i<response.detail.length;i++) {  
              if (relations.includes(response.detail[i].loc[2])) {
                const index = response.detail[i].loc[3];
                const fieldName = response.detail[i].loc[4];                
                message[`${response.detail[i].loc[2]}.${index}.${fieldName}`] = t(response.detail[i].msg);                                
              } else {          
                message[response.detail[i].loc[2]] = t(response.detail[i].msg);  
              }                              
            }
            setServerErrors(message);
            toast.error(t('error-occured')); 
          } else {
            if (response.detail[0] && response.detail[0].error) {
              toast.error(t(response.detail[0].error[0]));
            } else {
              toast.error(t('error-occured'));
            }
          }
        }
      }
    ).catch(() => {
      setDisableSubmit(false);
      toast.error(t('error-occured'));
    });
  }

  const closeAndUpdateEditModal = (data) => {
    setEditModalShow(false);
    if (entities.length === 0) {
      setEntities([data]);
      setNoEntity(false);
      setCurrentTab(data.active?'active':'inactive');
      setCount(1);
      setPages(1);
      setStart(1);
      setEnd(1);
    } else {
      setCurrentTab(data.active?'active':'inactive');
      setRefresh(prev => !prev);
    }
  };
 
  const handleSelectTab = (tab) => {
    if (tab !== currentTab) {
      setCurrentTab(tab);
      if (tab === 'active') setPage(pageActive);
      if (tab === 'inactive') setPage(pageInactive);
    }
  };

  useEffect(() => {
    setPageActive(page);
    setPageInactive(page);
    var status = null;
    var searchTerm = "";
    if (props.activeTabs) status = currentTab;
    CommonService.getEntities(props.app, props.entity, status, searchTerm, page, extraParams, entityPageSize).then(
      (data) => {
        if (!data.items) return;
        if (noEntity && currentTab && data.items.length === 0 && currentTab === 'active') {
          setCurrentTab('inactive');
          return;
        }
        if (data.items.length > 0) setNoEntity(false);
        setEntities(data.items);
        setCount(data.count);
        setPages(Math.ceil(data.count / entityPageSize));
        setStart((page - 1) * entityPageSize + 1);
        setEnd(data.items.length > 0 ? Math.min(((page - 1) * entityPageSize + 1) + data.items.length - 1, data.count) : 1);
        setWait(false);
      }
    );
  }, [refresh, currentTab, page, extraParamsKey, entityPageSize]);// eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setPage(1);
    setNoEntity(true);
    setWait(true);
    setRefresh(prev => !prev);
  }, [JSON.stringify(props.extraParams)]);// eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (props.user) {
      const query = new URLSearchParams(location.search);
      if (query.get('add')) {
        handleEdit();
      }
    }
  }, [location.search]);// eslint-disable-line react-hooks/exhaustive-deps
  
  return (
    <>   
      <header className="page-header-row">
        <h2>{t(`${props.entity}s`)}</h2>
        {props.renderMenu && props.renderMenu(handleEdit)}
      </header>
      {props.renderFilter && props.renderFilter()}
      <div>
        { !wait &&
          <>
            { noEntity ?
              <>
                {props.renderAlternative ?
                  <>
                    {props.renderAlternative(handleEdit)}
                  </>
                :
                  <>
                    {t(`no-${props.entity}-yet-add-first`)}&nbsp;
                    <span className="link action" onClick={() => handleEdit()}>
                      <AddCircleOutline color={COLOR_LINK} title={t(`add-${props.entity}`)} height="30px" width="30px"/>
                    </span> 
                  </>
                }
              </>
            :
              <>
                { props.activeTabs ?
                  <Tabs
                    defaultActiveKey="active"
                    id="projection-tab"
                    activeKey={currentTab}
                    onSelect={(tab) => handleSelectTab(tab)}
                    className="mb-3"
                  >
                    <Tab eventKey="active" title={t('active')}>
                      <Container>
                        <div className="text-left p-2">
                          {count > 1 && <> <Badge>{start}</Badge> {t('count-to')} <Badge>{end}</Badge> {t('count-of')} </> } <Badge>{count}</Badge>
                        </div>
                        <props.list
                          entities={entities}
                          active={true}
                          handleEdit={handleEdit}
                          handleDelete={handleDelete}
                          handleRefresh={handleRefresh}
                        />
                        <MigratisPagination
                          page={page}
                          pages={pages}
                          pageSize={pageSize}
                          setPage={setPage}
                        />
                      </Container>
                    </Tab>
                    <Tab eventKey="inactive" title={t('inactive')}>
                      <Container>
                        <div className="text-left p-2">
                          {count > 1 && <> <Badge>{start}</Badge> {t('count-to')} <Badge>{end}</Badge> {t('count-of')} </> } <Badge>{count}</Badge>
                        </div>
                        <props.list
                          entities={entities}
                          active={false}
                          handleEdit={handleEdit}
                          handleDelete={handleDelete}
                          handleRefresh={handleRefresh}
                        />
                        <MigratisPagination
                          page={page}
                          pages={pages}
                          pageSize={pageSize}
                          setPage={setPage}
                        />
                      </Container>
                    </Tab>
                  </Tabs>
                : 
                  <>
                    <div className="text-left p-2">
                          {count > 1 && <> <Badge>{start}</Badge> {t('count-to')} <Badge>{end}</Badge> {t('count-of')} </> } <Badge>{count}</Badge>
                    </div>                    
                    <props.list
                      entities={entities}
                      handleEdit={handleEdit}
                      handleDelete={handleDelete}
                      handleRefresh={handleRefresh}                       
                    />  
                    <MigratisPagination
                      page={page}
                      pages={pages}
                      pageSize={pageSize}
                      setPage={setPage}
                    /> 
                  </>
                }
              </>
            }
          </> 
        }               
      </div>
      <EditModal
        show={editModalShow}
        onHide={() => setEditModalShow(false)}
        title={entity?.id?t(`update-${props.entity}`):t(`add-${props.entity}`)}
      >
        <props.form
          entity={entity}
          serverErrors={serverErrors}
          disableSubmit={disableSubmit}
          saveEntity={saveEntity}
          {...(props.formProps || {})}
        />
      </EditModal>    
    </>
  );
}; 

export default Entities;
