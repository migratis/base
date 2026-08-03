import { Fragment, useState, useEffect, useMemo, useCallback } from "react";
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
import { PageShell, PagePanel } from './PageShell';
import { ITEMS_PER_PAGE as pageSize } from '../../settings';
import Badge from 'react-bootstrap/Badge';
import { Tabs, Tab } from 'react-bootstrap';
import Button from 'react-bootstrap/Button';
import { COLOR_LINK } from "../../settings";

// Rows and tables want to run edge to edge, so the panel drops its padding and
// clips them to its own radius.
const ListPanel = ({ children }) => (
  <PagePanel className="page-panel--flush">{children}</PagePanel>
);

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
          } else if (response.detail[0]?.loc) {
            const errorMsg = response.detail[0].msg;
            if (errorMsg) {
              toast.error(t(errorMsg));
            } else {
              toast.error(t('error-occured'));
            }
          } else {
            toast.error(t('error-occured'));
          }
        }
      );
    }
  };

  const handleDeleteAll = (active) => {
    if (window.confirm(t('confirm-delete-all-entities'))) {
      CommonService.deleteAllEntities(props.app, props.entity, active).then(
        (response) => {
          if (response.detail[0].success) {
            toast.success(t(response.detail[0].success[0], { count: response.deleted || 0 }));
            setRefresh(prev => !prev);
          } else if (response.detail[0].warning) {
            toast.warning(t(response.detail[0].warning[0]));
          } else if (response.detail[0]?.loc) {
            const errorMsg = response.detail[0].msg;
            if (errorMsg) {
              toast.error(t(errorMsg));
            } else {
              toast.error(t('error-occured'));
            }
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

  // Always re-read the saved row from the server. The first record used to be
  // painted straight from the submitted form data, which is everything the user
  // typed and nothing the server derived from it — no id, and for an
  // application no `needs_ai_regeneration`, the flag the "generate with AI"
  // sparkle hangs off. A user's first application therefore came back without
  // its sparkle until the page was reloaded by hand.
  const closeAndUpdateEditModal = (data) => {
    setEditModalShow(false);
    setNoEntity(false);
    setCurrentTab(data.active === false ? 'inactive' : 'active');
    setRefresh(prev => !prev);
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
  
  // Record count, plus the bulk-delete affordance when the caller asks for it.
  // `bulkDelete` is an opt-in *prop*: this used to be inferred from
  // `app === 'generator' && entity === 'entity'`, which taught a generic list
  // component the name of one feature module and silently denied the
  // affordance to every other caller. The endpoint behind it
  // (`/{app}/{entity}/delete-all`) was always generic.
  //
  // `active` scopes the deletion to the tab in view (true/false), or null for
  // an untabbed list — it is the same argument the tab renders under.
  const renderCountToolbar = (active) => (
    <div className="entities-toolbar d-flex justify-content-between align-items-center">
      <div>
        {count > 1 && <> <Badge>{start}</Badge> {t('count-to')} <Badge>{end}</Badge> {t('count-of')} </> } <Badge>{count}</Badge>
      </div>
      {count > 0 && props.bulkDelete && (
        <Button variant="outline-danger" size="sm" onClick={() => handleDeleteAll(active)}>
          {t('delete-all')}
        </Button>
      )}
    </div>
  );

  // Lists that bring their own surfaces (the application card grid) opt out of
  // the panel; row/table lists sit on a flush one so the rows reach its edges.
  const Surface = props.panel === false ? Fragment : ListPanel;

  return (
    <PageShell
      title={t(`${props.entity}s`)}
      description={props.description}
      actions={props.renderMenu && props.renderMenu(handleEdit)}
      width={props.width || 'wide'}
      panel={false}
      sticky
    >
      {props.renderFilter && props.renderFilter()}
      <div>
        { !wait &&
          <>
            { noEntity ?
              <PagePanel className="page-panel--empty">
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
              </PagePanel>
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
                      <Surface>
                        {renderCountToolbar(true)}
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
                      </Surface>
                    </Tab>
                    <Tab eventKey="inactive" title={t('inactive')}>
                      <Surface>
                        {renderCountToolbar(false)}
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
                      </Surface>
                    </Tab>
                  </Tabs>
:
                  <Surface>
                    {renderCountToolbar(null)}
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
                  </Surface>
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
        {/* Spread props.formProps so callers can pass extra context to the
            form (e.g. EntityForm / FieldForm need `applicationRoles` to
            render the per-app role dropdown; without this forward they
            silently fall back to the legacy public/user/admin triple). */}
        <props.form
          entity={entity}
          serverErrors={serverErrors}
          disableSubmit={disableSubmit}
          saveEntity={saveEntity}
          {...(props.formProps || {})}
        />
      </EditModal>
    </PageShell>
  );
};

export default Entities;
