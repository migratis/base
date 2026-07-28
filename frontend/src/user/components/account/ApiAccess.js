import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import { FormProvider, useForm } from 'react-hook-form';
import { toast } from 'react-toastify';
import {
  IoCopyOutline as CopyOutline,
  IoTrashOutline as TrashOutline,
  IoKeyOutline as KeyOutline,
} from 'react-icons/io5';
import UserService from "../../services/user.service";
import InputField from '../../../common/fields/InputField';
import DateField from '../../../common/fields/DateField';
import { LoaderIndicator } from '../../../common/components/LoaderIndicator';
import { CommonModal as ConfirmRevokeModal } from '../../../common/modals/CommonModal';
import { firstEnabled } from '../../../common/shell/collect';
import { tokenDocs } from '../../../common/shell/registry';

// "API access" section of the Account settings page: mint, list, and revoke
// the Personal Access Tokens that authenticate the agent lane. The raw secret
// is shown exactly once (the backend never returns it again), so the create
// flow surfaces a copy-now panel with a clear "you won't see this again" warning.
const ApiAccess = () => {
  const { t } = useTranslation('account');
  const [ tokens, setTokens ] = useState(null);
  const [ refresh, setRefresh ] = useState(false);
  const [ disableSubmit, setDisableSubmit ] = useState(false);
  const [ newSecret, setNewSecret ] = useState(null);
  const [ confirmRevoke, setConfirmRevoke ] = useState(null);
  // Minting tokens is a user concern; documenting what they unlock belongs to
  // the module that exposes the token-authenticated API (see generator/shell.js).
  const docs = firstEnabled(tokenDocs);

  const methods = useForm({
    mode: 'onChange',
    defaultValues: { name: "", expires_at: null },
  });
  const { handleSubmit, reset } = methods;

  useEffect(() => {
    UserService.listTokens().then((response) => {
      setTokens(response.items || []);
    });
  }, [refresh]);

  const onSubmit = async (data) => {
    setDisableSubmit(true);
    const response = await UserService.createToken(data);
    setDisableSubmit(false);
    if (response.token) {
      setNewSecret(response);
      reset({ name: "", expires_at: null });
      setRefresh(!refresh);
    } else if (response.detail && response.detail[0]) {
      const block = response.detail[0];
      const msg = (block.error || block.expires_at || ['unknown-error'])[0];
      toast.error(t(msg));
    }
  };

  const copySecret = () => {
    if (newSecret && navigator.clipboard) {
      navigator.clipboard.writeText(newSecret.token);
      toast.success(t('token-copied'));
    }
  };

  const handleRevoke = () => {
    const id = confirmRevoke.id;
    setConfirmRevoke(null);
    UserService.revokeToken(id).then((response) => {
      if (response.detail && response.detail[0] && response.detail[0].success) {
        toast.success(t(response.detail[0].success[0]));
        setRefresh((r) => !r);
      } else {
        toast.error(t('token-revoke-failed'));
      }
    });
  };

  const fmtDate = (iso) => (iso ? new Date(iso).toLocaleDateString() : '—');

  return (
    <>
      <LoaderIndicator/>
      <h5><KeyOutline/> {t('api-access')}</h5>
      <p className="text-muted">{t('api-access-intro')}</p>

      {/* One-time secret panel — shown only right after creation. */}
      { newSecret &&
        <div className="alert alert-success" data-testid="new-secret-panel">
          <strong>{t('token-created-once')}</strong>
          <div className="input-group my-2">
            <input
              type="text"
              className="form-control"
              readOnly
              value={`Authorization: Bearer ${newSecret.token}`}
              data-testid="new-secret-value"
            />
            <button className="btn btn-outline-secondary" type="button" onClick={copySecret}>
              <CopyOutline/> {t('copy')}
            </button>
          </div>
          { docs &&
            <small>
              {t('token-docs-hint')}{' '}
              <a href={docs.path}>{t('token-docs-link')}</a>
            </small>
          }
          <div className="mt-2">
            <button className="btn btn-sm btn-secondary" onClick={() => setNewSecret(null)}>
              {t('dismiss')}
            </button>
          </div>
        </div>
      }

      {/* Create form. */}
      <FormProvider {...methods}>
        <form onSubmit={handleSubmit(onSubmit)} className="row g-2 mb-3">
          <div className="col-sm-5">
            <InputField name="name" label={t('token-name')} required={true} maxLength={100} />
          </div>
          <div className="col-sm-4">
            <DateField name="expires_at" label={t('token-expiry-optional')} minDate={new Date()} />
          </div>
          <div className="col-sm-3">
            <div className="migratis-field">
              <label className="d-none d-sm-block invisible" aria-hidden="true">{t('token-name')}</label>
              <button type="submit" className="btn btn-primary w-100" disabled={disableSubmit}>
                {t('create-token')}
              </button>
            </div>
          </div>
        </form>
      </FormProvider>

      {/* Token list. */}
      { tokens && tokens.length > 0 ?
        <table className="table table-sm" data-testid="token-table">
          <thead>
            <tr>
              <th>{t('token-name')}</th>
              <th>{t('token-prefix')}</th>
              <th>{t('token-last-used')}</th>
              <th>{t('token-expiry')}</th>
              <th>{t('token-status')}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            { tokens.map((tok) => (
              <tr key={tok.id} data-testid={`token-row-${tok.id}`}>
                <td>{tok.name || '—'}</td>
                <td><code>{tok.masked_prefix}</code></td>
                <td>{fmtDate(tok.last_used)}</td>
                <td>{fmtDate(tok.expires_at)}</td>
                <td>
                  { tok.active
                    ? <span className="badge bg-success">{t('token-active')}</span>
                    : <span className="badge bg-secondary">{t('token-revoked')}</span> }
                </td>
                <td>
                  { tok.active &&
                    <button
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => setConfirmRevoke(tok)}
                      data-testid={`revoke-${tok.id}`}
                    >
                      <TrashOutline/> {t('revoke')}
                    </button>
                  }
                </td>
              </tr>
            )) }
          </tbody>
        </table>
        : tokens &&
          <p className="text-muted">{t('no-tokens-yet')}</p>
      }

      <ConfirmRevokeModal
        show={confirmRevoke !== null}
        onHide={() => setConfirmRevoke(null)}
        title={t('confirm-revoke-title')}
      >
        <div className="text-center">
          {t('confirm-revoke-text')}
          <br/><br/>
          <button onClick={handleRevoke} className="btn btn-danger">
            {t('revoke')}
          </button>
        </div>
      </ConfirmRevokeModal>
    </>
  );
};

export default ApiAccess;
