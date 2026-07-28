import { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';
import { toast } from 'react-toastify';
import UserService from "../../services/user.service";
import { LoaderIndicator } from '../../../common/components/LoaderIndicator';
import { accountSections } from '../../../common/shell/registry';

const LANGUAGES = [
  { code: 'en', flag: '🇬🇧', label: 'English' },
  { code: 'fr', flag: '🇫🇷', label: 'Français' },
  { code: 'es', flag: '🇪🇸', label: 'Español' },
  { code: 'ro', flag: '🇷🇴', label: 'Română' },
];

// Account "Preferences" section. Language is persisted to User.language (the
// source of truth) and also switched in i18next so the change is immediate.
// The Header/MenuLeft quick-switcher remains a session convenience.
//
// Feature modules append their own preference blocks through the shell
// registry's `accountSections` slot (e.g. the generator's default-LLM picker),
// so this page stays free of imports from modules it does not own.
const Preferences = () => {
  const { t, i18n } = useTranslation('account');
  const [ profile, setProfile ] = useState(null);
  const [ saving, setSaving ] = useState(false);
  const current = i18n.language?.substring(0, 2) || 'en';

  useEffect(() => {
    UserService.getProfile().then((response) => {
      if (!response.detail) setProfile(response);
    });
  }, []);

  const changeLanguage = async (code) => {
    if (saving || code === current) return;
    i18n.changeLanguage(code);
    localStorage.setItem('i18nextLng', code);
    if (!profile) return;
    setSaving(true);
    const response = await UserService.updateLanguage(profile, code);
    setSaving(false);
    if (response.detail && response.detail[0] && response.detail[0].success) {
      toast.success(t(response.detail[0].success[0]));
      setProfile({ ...profile, language: code });
    } else {
      toast.error(t('language-save-failed'));
    }
  };

  return (
    <>
      <LoaderIndicator/>
      <h5>{t('preferences')}</h5>
      <p className="text-muted">{t('language-intro')}</p>
      <div className="d-flex flex-wrap gap-2" data-testid="language-options">
        { LANGUAGES.map((lang) => (
          <button
            key={lang.code}
            type="button"
            className={`btn ${lang.code === current ? 'btn-primary' : 'btn-outline-secondary'}`}
            onClick={() => changeLanguage(lang.code)}
            disabled={saving}
            data-testid={`lang-${lang.code}`}
          >
            <span style={{ fontSize: '16px', marginRight: '6px' }}>{lang.flag}</span>
            {lang.label}
          </button>
        )) }
      </div>
      { accountSections
          .filter((slot) => slot.enabled())
          .map(({ id, Component }) => <Component key={id} />) }
    </>
  );
};

export default Preferences;
