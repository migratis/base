import { useState } from 'react';
import { useTranslation } from 'react-i18next';

const LANGUAGES = [
  { code: 'en', flag: '🇬🇧', label: 'English' },
  { code: 'fr', flag: '🇫🇷', label: 'Français' },
  { code: 'es', flag: '🇪🇸', label: 'Español' },
  { code: 'ro', flag: '🇷🇴', label: 'Română' },
];

const LangSelector = ({ compact = true }) => {
  const { i18n } = useTranslation();
  const currentLang = i18n.language?.substring(0, 2) || 'en';
  const [showDropdown, setShowDropdown] = useState(false);

  const changeLanguage = (code) => {
    i18n.changeLanguage(code);
    localStorage.setItem('i18nextLng', code);
    setShowDropdown(false);
  };

  const currentFlag = LANGUAGES.find(l => l.code === currentLang)?.flag || '🌐';
  const currentLabel = LANGUAGES.find(l => l.code === currentLang)?.label || 'Language';

  return (
    <div className="lang-selector-compact" style={{ position: 'relative' }}>
      <div 
        className="lang-selector-trigger"
        onClick={() => setShowDropdown(!showDropdown)}
        style={{ cursor: 'pointer' }}
      >
        <span style={{ fontSize: '16px' }}>{currentFlag}</span>
        {!compact && (
          <span className="sidebar-label" style={{ marginLeft: '8px' }}>
            {currentLabel}
          </span>
        )}
      </div>
      
      {showDropdown && (
        <div 
          className="lang-dropdown"
          style={{
            position: 'absolute',
            bottom: '100%',
            left: '0',
            background: 'var(--color-dark)',
            borderRadius: 'var(--border-radius)',
            padding: '8px',
            minWidth: '120px',
            boxShadow: 'var(--shadow-lg)',
            zIndex: 1001,
          }}
        >
          {LANGUAGES.map((lang) => (
            <div
              key={lang.code}
              onClick={() => changeLanguage(lang.code)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                cursor: 'pointer',
                borderRadius: 'var(--border-radius-sm)',
                backgroundColor: lang.code === currentLang ? 'rgba(255,255,255,0.1)' : 'transparent',
                color: lang.code === currentLang ? 'var(--color-light)' : 'rgba(255,255,255,0.7)',
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = lang.code === currentLang ? 'rgba(255,255,255,0.1)' : 'transparent'}
            >
              <span style={{ fontSize: '14px' }}>{lang.flag}</span>
              <span style={{ fontSize: '0.85rem' }}>{lang.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
  
export default LangSelector;
