"""
i18n/management/commands/seed_translations.py
---------------------------------------------
Single unified command that seeds ALL translation namespaces for the project.

Usage:
    python manage.py seed_translations
    python manage.py seed_translations --update   # overwrite existing texts
    python manage.py seed_translations --ns generator  # single namespace

Safe to re-run -- uses get_or_create everywhere.
"""

from django.core.management.base import BaseCommand
from migratis.i18n.models import TranslationNameSpace, TranslationKey, TranslationText


TRANSLATIONS = {}

# --------------------------------------------------------------------------- #
# NAMESPACE_LINKS
# Keys that already exist (texts already seeded in another namespace) that
# should simply be linked to one or more additional namespaces — no text
# duplication, just an M2M .add() call.
# Structure: { 'namespace': ['key1', 'key2', ...] }
# --------------------------------------------------------------------------- #
NAMESPACE_LINKS = {}

# Keys shared across application / entity / field (and already in generator):
_SHARED_CRUD = [
    'name', 'description', 'cdate', 'edit', 'delete', 'validate',
    'fields-mandatory', 'add', 'show-more', 'show-less',
    'confirm-delete-record', 'error-occured',
    'count-to', 'count-of',
    'successfully-saved', 'successfully-updated', 'successfully-deleted',
    'active', 'inactive',
]

NAMESPACE_LINKS['application'] = _SHARED_CRUD + [
    'status', 'status-draft', 'status-ongoing', 'status-generated',
    'ai-instructions', 'ai-instructions-app-help',
    'workflow-description', 'workflow-description-help',
    'modules-needed',
    'user-module', 'subscription-module', 'i18n-module', 'support-module', 'contact-module', 'cookie-module',
    'none', 'user-auto-selected-tooltip',
    'additional-languages', 'main-language',
    'select-language', 'select-languages',
    'cancel', 'continue', 'logo-regenerated',
]

NAMESPACE_LINKS['entity'] = _SHARED_CRUD + [
    'role', 'role-model', 'role-service', 'role-controller', 'role-utility',
    'ai-instructions', 'ai-instructions-help',
]

NAMESPACE_LINKS['field'] = _SHARED_CRUD + [
    'required', 'not-required',
    'ai-instructions', 'ai-instructions-help',
]

# ===========================================================================
# layout
# ===========================================================================
TRANSLATIONS['layout'] = {
    'migratis': {
        'en': 'Migratis',
        'fr': 'Migratis',
        'es': 'Migratis',
        'ro': 'Migratis',
    },
    'generator': {
        'en': 'Generator',
        'fr': 'Générateur',
        'es': 'Generador',
        'ro': 'Generator',
    },
    'documentation': {
        'en': 'Documentation',
        'fr': 'Documentation',
        'es': 'Documentación',
        'ro': 'Documentație',
    },
    'generator-documentation': {
        'en': 'Application Generator Documentation',
        'fr': 'Documentation du Générateur d\'Applications',
        'es': 'Documentación del Generador de Aplicaciones',
        'ro': 'Documentația Generatorului de Aplicații',
    },
    'items': {
        'en': 'Items',
        'fr': 'Éléments',
        'es': 'Elementos',
        'ro': 'Elemente',
    },
    'subitems': {
        'en': 'Subitems',
        'fr': 'Sous-éléments',
        'es': 'Subelementos',
        'ro': 'Subelemente',
    },
    'applications': {
        'en': 'Applications',
        'fr': 'Applications',
        'es': 'Aplicaciones',
        'ro': 'Aplicații',
    },
    'entities': {
        'en': 'Entities',
        'fr': 'Entités',
        'es': 'Entidades',
        'ro': 'Entități',
    },
    'fields': {
        'en': 'Fields',
        'fr': 'Champs',
        'es': 'Campos',
        'ro': 'Câmpuri',
    },
    'documentation': {
        'en': 'Documentation',
        'fr': 'Documentation',
        'es': 'Documentación',
        'ro': 'Documentație',
    },
    'contact': {
        'en': 'Contact',
        'fr': 'Contact',
        'es': 'Contacto',
        'ro': 'Contact',
    },
    'logout': {
        'en': 'Logout',
        'fr': 'Déconnexion',
        'es': 'Cerrar sesión',
        'ro': 'Deconectare',
    },
    'login': {
        'en': 'Login',
        'fr': 'Se connecter',
        'es': 'Iniciar sesión',
        'ro': 'Autentificare',
    },
    'register': {
        'en': 'Register',
        'fr': "S'inscrire",
        'es': 'Registrarse',
        'ro': 'Înregistrare',
    },
    'profile': {
        'en': 'Profile',
        'fr': 'Profil',
        'es': 'Perfil',
        'ro': 'Profil',
    },
    'subscribe': {
        'en': 'Subscribe',
        'fr': "S'abonner",
        'es': 'Suscribirse',
        'ro': 'Abonează-te',
    },
    'support': {
        'en': 'Support',
        'fr': 'Support',
        'es': 'Soporte',
        'ro': 'Suport',
    },
    'collapse-menu': {
        'en': 'Collapse menu',
        'fr': 'Réduire le menu',
        'es': 'Colapsar menú',
        'ro': 'Restrânge meniul',
    },
    'expand-menu': {
        'en': 'Expand menu',
        'fr': 'Développer le menu',
        'es': 'Expandir menú',
        'ro': 'Extinde meniul',
    },
    'my-menu': {
        'en': 'My menu',
        'fr': 'Mon menu',
        'es': 'Mi menú',
        'ro': 'Meniul meu',
    },
    'details': {
        'en': 'Details',
        'fr': 'Détails',
        'es': 'Detalles',
        'ro': 'Detalii',
    },
    'select-language': {
        'en': 'Select language',
        'fr': 'Sélectionner la langue',
        'es': 'Seleccionar idioma',
        'ro': 'Selectează limba',
    },
    'session-expired': {
        'en': 'Session Expired',
        'fr': 'Session expirée',
        'es': 'Sesión expirada',
        'ro': 'Sesiune expirată',
    },
}

# ===========================================================================
# activate
# ===========================================================================
TRANSLATIONS['activate'] = {
    'email-activation': {
        'en': 'Email confirmation',
        'fr': 'Confirmation du couriel',
        'es': 'Confirmación del correo electrónico',
        'ro': 'Confirmare email',
    },
    'error-occured': {
        'en': 'Error in the form !',
        'fr': 'Erreur dans le formulaire !',
        'es': '¡Error en el formulario!',
        'ro': 'Eroare în formular!',
    },
    'login': {
        'en': 'Login',
        'fr': 'Se connecter',
        'es': 'Iniciar sesión',
        'ro': 'Autentificare',
    },
    'password-already-used': {
        'en': 'Password already used',
        'fr': 'Ce mot de passe a déjà été utilisé',
        'es': 'Contraseña ya utilizada',
        'ro': 'Parolă deja utilizată',
    },
    'register': {
        'en': 'Register',
        'fr': "S'enregistrer",
        'es': 'Registrarse',
        'ro': 'Înregistrează-te',
    },
    'registration-confirmation-done': {
        'en': 'Activation already done.',
        'fr': "L'activation a déjà été faite.",
        'es': 'Activación ya realizada.',
        'ro': 'Activarea a fost deja efectuată.',
    },
    'registration-confirmation-failed': {
        'en': 'Your profile activation has failed, please reset your password',
        'fr': "L'activation de votre profil a échouée, veuillez réinitialiser votre mot de passe",
        'es': 'La activación de tu perfil ha fallado, por favor restablece tu contraseña.',
        'ro': 'Activarea profilului tău a eșuat, te rugăm să îți resetezi parola.',
    },
    'registration-confirmed': {
        'en': 'Your profile is now activated, you can log in.',
        'fr': 'Votre profil est maintenant activé, vous pouvez vous connecter.',
        'es': 'Tu perfil ya está activado, puedes iniciar sesión.',
        'ro': 'Profilul tău este acum activat, te poți autentifica.',
    },
    'try-again-later': {
        'en': 'Try again later.',
        'fr': 'Essayez plus tard.',
        'es': 'Inténtalo de nuevo más tarde.',
        'ro': 'Încearcă din nou mai târziu.',
    },
    'user-not-exists': {
        'en': 'Unknown user',
        'fr': 'Utilisateur inconnu',
        'es': 'Usuario desconocido',
        'ro': 'Utilizator necunoscut',
    },
    'validate': {
        'en': 'Validate',
        'fr': 'Valider',
        'es': 'Validar',
        'ro': 'Validează',
    },
}

# ===========================================================================
# cookie
# ===========================================================================
TRANSLATIONS['cookie'] = {
    'cookies-list': {
        'en': 'Cookie list of the site',
        'fr': 'Liste des cookies du site',
        'es': 'Lista de cookies del sitio',
        'ro': 'Lista de cookie-uri a site-ului',
    },
    'csrftoken': {
        'en': 'Protective token against cross site request forgery.',
        'fr': 'Jeton de protection contre la contrefaçon de requête inter-site.',
        'es': 'Token de protección contra la falsificación de solicitudes entre sitios',
        'ro': 'Token de protecție împotriva falsificării cererilor între site-uri',
    },
    'description': {
        'en': 'Description',
        'fr': 'Description',
        'es': 'Descripción',
        'ro': 'Descriere',
    },
    'i18next': {
        'en': 'Cookie to keep the navigation language',
        'fr': 'Cookie de mémorisation de la langue de navigation',
        'es': 'Cookie para mantener el idioma de navegación',
        'ro': 'Cookie pentru a păstra limba de navigare',
    },
    'name': {
        'en': 'Name',
        'fr': 'Nom',
        'es': 'Nombre',
        'ro': 'Nume',
    },
    'provider': {
        'en': 'Provider',
        'fr': 'Fournisseur',
        'es': 'Proveedor',
        'ro': 'Furnizor',
    },
    'sessionid': {
        'en': 'Session and internal authentication token.',
        'fr': "Jeton de session et d'authentification interne.",
        'es': 'Sesión y token interno de autenticación',
        'ro': 'Sesiune și token intern de autentificare',
    },
    'spcc1': {
        'en': 'cookie consent cookies of the site',
        'fr': 'Cookie de consentement des cookies du site',
        'es': 'Cookies de consentimiento del sitio',
        'ro': 'Cookie-uri de consimțământ ale site-ului',
    },
    '__stripe_mid': {
        'en': 'Cookie set to provide fraud prevention. Stripe is our payment partner.',
        'fr': 'Cookie placé par notre partenaire de paiement Stripe, pour prévenir la fraude.',
        'es': 'Cookie establecida para prevenir el fraude. Stripe es nuestro socio de pagos.',
        'ro': 'Cookie setat pentru prevenirea fraudei. Stripe este partenerul nostru de plăți.',
    },
    '__stripe_sid': {
        'en': 'Session cookie set by Stripe, our payment partner.',
        'fr': 'Cookie de session placé par notre partenaire de paiement Stripe.',
        'es': 'Cookie de sesión establecida por Stripe, nuestro socio de pagos.',
        'ro': 'Cookie de sesiune setat de Stripe, partenerul nostru de plăți.',
    },
}

# ===========================================================================
# email
# ===========================================================================
TRANSLATIONS['email'] = {
    'change-password': {
        'en': 'Password change',
        'fr': 'Changement de mot de passe',
        'es': 'Cambio de contraseña',
        'ro': 'Schimbare parolă',
    },
    'confirm-registration': {
        'en': 'Profile activation',
        'fr': 'Activation de votre profil',
        'es': 'Activación del perfil',
        'ro': 'Activarea profilului',
    },
    'invitation-to-register': {
        'en': 'Sharing of projection (need your registering first)',
        'fr': "Partage d'une projection (inscription nécessaire)",
        'es': 'Compartir la proyección (es necesario registrarse primero)',
        'ro': 'Partajarea proiecției (este necesară înregistrarea mai întâi)',
    },
    'projection-shared': {
        'en': 'Shared projection',
        'fr': 'Projection partagée',
        'es': 'Proyección compartida',
        'ro': 'Proiecție partajată',
    },
}

# ===========================================================================
# form
# ===========================================================================
TRANSLATIONS['form'] = {
    'empty-field': {
        'en': 'This field cannot be empty',
        'fr': 'Ce champ ne peut pas être vide',
        'es': 'Este campo no puede estar vacío',
        'ro': 'Acest câmp nu poate fi gol',
    },
    'error-occured': {
        'en': 'Error in the form !',
        'fr': 'Erreur dans le formulaire !',
        'es': '¡Error en el formulario!',
        'ro': 'Eroare în formular!',
    },
    'Field required': {
        'en': 'This field cannot be empty',
        'fr': 'Ce champ ne peut pas être vide',
        'es': 'Este campo no puede estar vacío',
        'ro': 'Acest câmp nu poate fi gol',
    },
    'Input should be a valid decimal': {
        'en': 'This is not a number',
        'fr': "Ceci n'est pas un nombre",
        'es': 'No es un número',
        'ro': 'Nu este un număr',
    },
    'max-length-exceeded': {
        'en': 'Max length exceeded',
        'fr': 'Taille maximale dépassée',
        'es': 'Longitud máxima superada',
        'ro': 'Lungime maximă depășită',
    },
    'reset': {
        'en': 'Empty',
        'fr': 'Vider',
        'es': 'Vacío',
        'ro': 'Gol',
    },
    'select-date': {
        'en': 'Select a date',
        'fr': 'Sélectionnez une date',
        'es': 'Selecciona una fecha',
        'ro': 'Selectează o dată',
    },
    'value is not a valid email address: An email address must have an @-sign': {
        'en': 'value is not a valid email address: An email address must have an @-sign',
        'fr': "Ceci n'est pas un courriel valide, il doit au moins contenir le signe @",
        'es': 'El valor no es una dirección de correo electrónico válida: una dirección de correo electrónico debe tener un signo @',
        'ro': 'Valoarea nu este o adresă de email validă: o adresă de email trebuie să conțină un semn @',
    },
}

# ===========================================================================
# installer
# ===========================================================================
TRANSLATIONS['installer'] = {
    'installer-title': {
        'en': 'Installer', 'fr': 'Installateur', 'es': 'Instalador', 'ro': 'Instalator',
    },
    'connect-to-migratis': {
        'en': 'Connect to Migratis', 'fr': 'Se connecter à Migratis',
        'es': 'Conectarse a Migratis', 'ro': 'Conectează-te la Migratis',
    },
    'email': {
        'en': 'Email', 'fr': 'Courriel', 'es': 'Correo electrónico', 'ro': 'Email',
    },
    'password': {
        'en': 'Password', 'fr': 'Mot de passe', 'es': 'Contraseña', 'ro': 'Parolă',
    },
    'migratis-url': {
        'en': 'Migratis URL', 'fr': 'URL Migratis', 'es': 'URL de Migratis', 'ro': 'URL Migratis',
    },
    'leave-blank-default': {
        'en': '(leave blank for default)', 'fr': '(laisser vide pour la valeur par défaut)',
        'es': '(dejar en blanco para el valor predeterminado)', 'ro': '(lăsați gol pentru valoarea implicită)',
    },
    'connect': {
        'en': 'Connect', 'fr': 'Se connecter', 'es': 'Conectar', 'ro': 'Conectează-te',
    },
    'disconnect': {
        'en': 'Disconnect', 'fr': 'Se déconnecter', 'es': 'Desconectar', 'ro': 'Deconectează-te',
    },
    'select-app': {
        'en': 'Select an application to install', 'fr': 'Sélectionnez une application à installer',
        'es': 'Seleccione una aplicación para instalar', 'ro': 'Selectați o aplicație de instalat',
    },
    'no-apps': {
        'en': 'No generated applications found.', 'fr': 'Aucune application générée trouvée.',
        'es': 'No se encontraron aplicaciones generadas.', 'ro': 'Nu s-au găsit aplicații generate.',
    },
    'module-label': {
        'en': 'module:', 'fr': 'module :', 'es': 'módulo:', 'ro': 'modul:',
    },
    'installed-badge': {
        'en': 'Installed', 'fr': 'Installé', 'es': 'Instalado', 'ro': 'Instalat',
    },
    'install-selected': {
        'en': 'Install selected app', 'fr': "Installer l'application sélectionnée",
        'es': 'Instalar la aplicación seleccionada', 'ro': 'Instalează aplicația selectată',
    },
    'install-another': {
        'en': 'Install another', 'fr': 'En installer une autre',
        'es': 'Instalar otra', 'ro': 'Instalează alta',
    },
    'installed-modules': {
        'en': 'Installed modules', 'fr': 'Modules installés',
        'es': 'Módulos instalados', 'ro': 'Module instalate',
    },
    'uninstall': {
        'en': 'Uninstall', 'fr': 'Désinstaller', 'es': 'Desinstalar', 'ro': 'Dezinstalează',
    },
    'uninstalling': {
        'en': 'Uninstalling…', 'fr': 'Désinstallation…', 'es': 'Desinstalando…', 'ro': 'Se dezinstalează…',
    },
    'uninstall-result': {
        'en': 'Uninstall result', 'fr': 'Résultat de la désinstallation',
        'es': 'Resultado de la desinstalación', 'ro': 'Rezultatul dezinstalării',
    },
    'uninstalled-success': {
        'en': 'Module {{module}} uninstalled successfully.',
        'fr': 'Module {{module}} désinstallé avec succès.',
        'es': 'Módulo {{module}} desinstalado correctamente.',
        'ro': 'Modulul {{module}} a fost dezinstalat cu succes.',
    },
    'migrations-reverted': {
        'en': 'Migrations reverted.', 'fr': 'Migrations annulées.',
        'es': 'Migraciones revertidas.', 'ro': 'Migrările au fost anulate.',
    },
    'migration-revert-failed': {
        'en': 'Warning: migration revert failed — check output below.',
        'fr': "Avertissement : l'annulation de la migration a échoué — vérifiez la sortie ci-dessous.",
        'es': 'Advertencia: la reversión de la migración falló — revise la salida a continuación.',
        'ro': 'Avertisment: anularea migrării a eșuat — verificați rezultatul de mai jos.',
    },
    'restart-to-complete-removal': {
        'en': 'Restart the backend container to complete the removal:',
        'fr': 'Redémarrez le conteneur backend pour terminer la suppression :',
        'es': 'Reinicie el contenedor del backend para completar la eliminación:',
        'ro': 'Reporniți containerul backend pentru a finaliza eliminarea:',
    },
    'back': {
        'en': 'Back', 'fr': 'Retour', 'es': 'Volver', 'ro': 'Înapoi',
    },
    'tfa-title': {
        'en': 'Two-factor authentication',
        'fr': 'Authentification à deux facteurs',
        'es': 'Autenticación de dos factores',
        'ro': 'Autentificare în doi pași',
    },
    'tfa-help': {
        'en': 'Enter the verification code we emailed to {{email}}.',
        'fr': 'Saisissez le code de vérification que nous avons envoyé à {{email}}.',
        'es': 'Introduzca el código de verificación que enviamos a {{email}}.',
        'ro': 'Introduceți codul de verificare trimis prin email la {{email}}.',
    },
    'tfa-code': {
        'en': 'Verification code', 'fr': 'Code de vérification',
        'es': 'Código de verificación', 'ro': 'Cod de verificare',
    },
    'tfa-verify': {
        'en': 'Verify', 'fr': 'Vérifier', 'es': 'Verificar', 'ro': 'Verifică',
    },
    'tfa-code-required': {
        'en': 'Please enter the verification code.',
        'fr': 'Veuillez saisir le code de vérification.',
        'es': 'Introduzca el código de verificación.',
        'ro': 'Introduceți codul de verificare.',
    },
    'tfa-code-invalid': {
        'en': 'Invalid verification code.', 'fr': 'Code de vérification invalide.',
        'es': 'Código de verificación no válido.', 'ro': 'Cod de verificare invalid.',
    },
    'tfa-code-expired': {
        'en': 'The verification code has expired. Please reconnect to get a new one.',
        'fr': 'Le code de vérification a expiré. Veuillez vous reconnecter pour en obtenir un nouveau.',
        'es': 'El código de verificación ha caducado. Vuelva a conectarse para obtener uno nuevo.',
        'ro': 'Codul de verificare a expirat. Reconectați-vă pentru a primi unul nou.',
    },
    'tfa-max-attempts': {
        'en': 'Too many invalid attempts. Please reconnect to get a new code.',
        'fr': 'Trop de tentatives invalides. Veuillez vous reconnecter pour obtenir un nouveau code.',
        'es': 'Demasiados intentos no válidos. Vuelva a conectarse para obtener un nuevo código.',
        'ro': 'Prea multe încercări invalide. Reconectați-vă pentru a primi un cod nou.',
    },
    'installer-disabled': {
        'en': 'The installer is currently disabled.',
        'fr': "L'installateur est actuellement désactivé.",
        'es': 'El instalador está actualmente desactivado.',
        'ro': 'Instalatorul este momentan dezactivat.',
    },
    'installer-disabled-set': {
        'en': 'To re-enable it, set this in backend/migratis/.env:',
        'fr': 'Pour le réactiver, définissez ceci dans backend/migratis/.env :',
        'es': 'Para reactivarlo, configure esto en backend/migratis/.env:',
        'ro': 'Pentru a-l reactiva, setați aceasta în backend/migratis/.env:',
    },
    'installer-disabled-restart': {
        'en': 'Then restart the backend:',
        'fr': 'Puis redémarrez le backend :',
        'es': 'Luego reinicie el backend:',
        'ro': 'Apoi reporniți backendul:',
    },
    'error-label': {
        'en': 'Error', 'fr': 'Erreur', 'es': 'Error', 'ro': 'Eroare',
    },
    'installed-success': {
        'en': 'Module "{{module}}" installed successfully.',
        'fr': 'Module « {{module}} » installé avec succès.',
        'es': 'Módulo «{{module}}» instalado correctamente.',
        'ro': 'Modulul „{{module}}” a fost instalat cu succes.',
    },
    'install-failed-msg': {
        'en': 'Installation failed.', 'fr': "L'installation a échoué.",
        'es': 'La instalación falló.', 'ro': 'Instalarea a eșuat.',
    },
    'backend-migration': {
        'en': 'Backend migration:', 'fr': 'Migration backend :',
        'es': 'Migración del backend:', 'ro': 'Migrare backend:',
    },
    'seed-translations': {
        'en': 'Seed translations:', 'fr': 'Initialiser les traductions :',
        'es': 'Sembrar traducciones:', 'ro': 'Inițializare traduceri:',
    },
    'frontend-files': {
        'en': 'Frontend files:', 'fr': 'Fichiers frontend :',
        'es': 'Archivos del frontend:', 'ro': 'Fișiere frontend:',
    },
    'applied-on-restart': {
        'en': 'Applied automatically on restart', 'fr': 'Appliqué automatiquement au redémarrage',
        'es': 'Aplicado automáticamente al reiniciar', 'ro': 'Aplicat automat la repornire',
    },
    'ok': {
        'en': 'OK', 'fr': 'OK', 'es': 'OK', 'ro': 'OK',
    },
    'failed': {
        'en': 'Failed', 'fr': 'Échec', 'es': 'Falló', 'ro': 'Eșuat',
    },
    'installed-automatically': {
        'en': 'Installed automatically', 'fr': 'Installé automatiquement',
        'es': 'Instalado automáticamente', 'ro': 'Instalat automat',
    },
    'not-applied-volume': {
        'en': 'Not applied (volume not mounted)', 'fr': 'Non appliqué (volume non monté)',
        'es': 'No aplicado (volumen no montado)', 'ro': 'Neaplicat (volum nemontat)',
    },
    'almost-done': {
        'en': 'Almost done!', 'fr': 'Presque terminé !', 'es': '¡Casi listo!', 'ro': 'Aproape gata!',
    },
    'restart-to-load-module': {
        'en': 'Restart the backend container to load the new module:',
        'fr': 'Redémarrez le conteneur backend pour charger le nouveau module :',
        'es': 'Reinicie el contenedor del backend para cargar el nuevo módulo:',
        'ro': 'Reporniți containerul backend pentru a încărca noul modul:',
    },
    'rebuild-static-assets': {
        'en': 'If your frontend is served by nginx, also rebuild the static assets:',
        'fr': 'Si votre frontend est servi par nginx, reconstruisez aussi les fichiers statiques :',
        'es': 'Si su frontend es servido por nginx, reconstruya también los recursos estáticos:',
        'ro': 'Dacă frontendul este servit de nginx, reconstruiți și fișierele statice:',
    },
    'confirm-uninstall': {
        'en': 'Uninstall "{{module}}"?\n\nThis will revert all migrations and remove all files for this module.',
        'fr': 'Désinstaller « {{module}} » ?\n\nCela annulera toutes les migrations et supprimera tous les fichiers de ce module.',
        'es': '¿Desinstalar «{{module}}»?\n\nEsto revertirá todas las migraciones y eliminará todos los archivos de este módulo.',
        'ro': 'Dezinstalați „{{module}}”?\n\nAceasta va anula toate migrările și va elimina toate fișierele acestui modul.',
    },
    # ── backend error codes (rendered via t(code)) ──────────────────────────
    'connection-failed': {
        'en': 'Could not connect to the Migratis instance.',
        'fr': "Impossible de se connecter à l'instance Migratis.",
        'es': 'No se pudo conectar a la instancia de Migratis.',
        'ro': 'Nu s-a putut conecta la instanța Migratis.',
    },
    'invalid-credentials': {
        'en': 'Invalid email or password.', 'fr': 'Courriel ou mot de passe invalide.',
        'es': 'Correo o contraseña no válidos.', 'ro': 'Email sau parolă invalidă.',
    },
    'missing-credentials': {
        'en': 'Please enter your email and password.',
        'fr': 'Veuillez saisir votre courriel et votre mot de passe.',
        'es': 'Introduzca su correo y contraseña.',
        'ro': 'Introduceți emailul și parola.',
    },
    'invalid-request': {
        'en': 'Invalid request.', 'fr': 'Requête invalide.',
        'es': 'Solicitud no válida.', 'ro': 'Cerere invalidă.',
    },
    'not-connected': {
        'en': 'Not connected. Please reconnect.', 'fr': 'Non connecté. Veuillez vous reconnecter.',
        'es': 'No conectado. Vuelva a conectarse.', 'ro': 'Neconectat. Reconectați-vă.',
    },
    'install-failed': {
        'en': 'Installation failed.', 'fr': "L'installation a échoué.",
        'es': 'La instalación falló.', 'ro': 'Instalarea a eșuat.',
    },
    'download-failed': {
        'en': 'Failed to download the application.',
        'fr': "Échec du téléchargement de l'application.",
        'es': 'Error al descargar la aplicación.',
        'ro': 'Descărcarea aplicației a eșuat.',
    },
    'uninstall-failed': {
        'en': 'Uninstallation failed.', 'fr': 'La désinstallation a échoué.',
        'es': 'La desinstalación falló.', 'ro': 'Dezinstalarea a eșuat.',
    },
    # ── Install-time configuration step ───────────────────────────────────
    'config-title': {
        'en': 'Configure {{app}}', 'fr': 'Configurer {{app}}',
        'es': 'Configurar {{app}}', 'ro': 'Configurează {{app}}',
    },
    'config-help': {
        'en': 'This app needs a few settings to work. Leave a field blank to set it later in the environment file.',
        'fr': "Cette application a besoin de quelques réglages pour fonctionner. Laissez un champ vide pour le définir plus tard dans le fichier d'environnement.",
        'es': 'Esta aplicación necesita algunos ajustes para funcionar. Deje un campo en blanco para definirlo más tarde en el archivo de entorno.',
        'ro': 'Această aplicație are nevoie de câteva setări pentru a funcționa. Lăsați un câmp gol pentru a-l defini mai târziu în fișierul de mediu.',
    },
    'config-admin': {
        'en': 'Administrator account', 'fr': 'Compte administrateur',
        'es': 'Cuenta de administrador', 'ro': 'Cont de administrator',
    },
    'admin-email': {
        'en': 'Admin email', 'fr': "Courriel de l'administrateur",
        'es': 'Correo del administrador', 'ro': 'Email administrator',
    },
    'admin-password': {
        'en': 'Admin password', 'fr': "Mot de passe de l'administrateur",
        'es': 'Contraseña del administrador', 'ro': 'Parolă administrator',
    },
    'config-email': {
        'en': 'Email (SMTP) transport', 'fr': 'Transport courriel (SMTP)',
        'es': 'Transporte de correo (SMTP)', 'ro': 'Transport email (SMTP)',
    },
    'smtp-host': {
        'en': 'SMTP host', 'fr': 'Hôte SMTP', 'es': 'Host SMTP', 'ro': 'Gazdă SMTP',
    },
    'smtp-user': {
        'en': 'SMTP user', 'fr': 'Utilisateur SMTP',
        'es': 'Usuario SMTP', 'ro': 'Utilizator SMTP',
    },
    'smtp-password': {
        'en': 'SMTP password', 'fr': 'Mot de passe SMTP',
        'es': 'Contraseña SMTP', 'ro': 'Parolă SMTP',
    },
    'email-sender': {
        'en': 'Sender address', 'fr': "Adresse d'expéditeur",
        'es': 'Dirección del remitente', 'ro': 'Adresă expeditor',
    },
    'email-moderator': {
        'en': 'Moderator address', 'fr': 'Adresse du modérateur',
        'es': 'Dirección del moderador', 'ro': 'Adresă moderator',
    },
    'config-stripe': {
        'en': 'Stripe keys', 'fr': 'Clés Stripe',
        'es': 'Claves de Stripe', 'ro': 'Chei Stripe',
    },
    'stripe-publishable': {
        'en': 'Publishable key', 'fr': 'Clé publiable',
        'es': 'Clave publicable', 'ro': 'Cheie publicabilă',
    },
    'stripe-secret': {
        'en': 'Secret key', 'fr': 'Clé secrète',
        'es': 'Clave secreta', 'ro': 'Cheie secretă',
    },
    'stripe-webhook': {
        'en': 'Webhook signing secret', 'fr': 'Secret de signature du webhook',
        'es': 'Secreto de firma del webhook', 'ro': 'Secret de semnare webhook',
    },
}

# ===========================================================================
# generator
# ===========================================================================
TRANSLATIONS['generator'] = {
    'active': {
        'en': 'Active',
        'fr': 'Actif',
        'es': 'Activo',
        'ro': 'Activ',
    },
    'add': {
        'en': 'Add',
        'fr': 'Ajouter',
        'es': 'Agregar',
        'ro': 'Adaugă',
    },
    'add-application': {
        'en': 'Add application',
        'fr': 'Ajouter une application',
        'es': 'Agregar aplicación',
        'ro': 'Adaugă aplicație',
    },
    'add-entity': {
        'en': 'Add entity',
        'fr': 'Ajouter une entité',
        'es': 'Agregar entidad',
        'ro': 'Adaugă entitate',
    },
    'add-field': {
        'en': 'Add field',
        'fr': 'Ajouter un champ',
        'es': 'Agregar campo',
        'ro': 'Adaugă câmp',
    },
    'add-relationship': {
        'en': 'Add relationship',
        'fr': 'Ajouter une relation',
        'es': 'Agregar relación',
        'ro': 'Adaugă relație',
    },
    'ai-building-model': {
        'en': 'AI is analysing your description and building your model. Navigate to Entities to see the result.',
        'fr': "L'IA analyse votre description et construit votre modèle. Naviguez vers Entités pour voir le résultat.",
        'es': 'La IA está analizando tu descripción y construyendo tu modelo. Navega a Entidades para ver el resultado.',
        'ro': 'AI-ul analizează descrierea și construiește modelul. Navigați la Entități pentru a vedea rezultatul.',
    },
    'ai-loading': {
        'en': 'Please wait while AI is processing your request...',
        'fr': "Veuillez patienter pendant que l'IA traite votre demande...",
        'es': 'Por favor espere mientras la IA procesa su solicitud...',
        'ro': 'Vă rugăm să așteptați în timp ce AI-ul procesează cererea dvs...',
    },
    'ai-calls': {
        'en': 'AI calls available: {{remaining}}',
        'fr': 'Appels IA disponibles : {{remaining}}',
        'es': 'Llamadas IA disponibles: {{remaining}}',
        'ro': 'Apeluri IA disponibile: {{remaining}}',
    },
    'custom-amount': {
        'en': 'Custom amount',
        'fr': 'Montant personnalisé',
        'es': 'Cantidad personalizada',
        'ro': 'Sumă personalizată',
    },
    'minimum-quantity': {
        'en': 'Minimum quantity is {{min}} extra AI calls',
        'fr': 'La quantité minimum est de {{min}} appels IA supplémentaires',
        'es': 'La cantidad mínima es de {{min}} llamadas de IA adicionales',
        'ro': 'Cantitatea minimă este de {{min}} apeluri IA suplimentare',
    },
    'ai-usage-click-to-buy': {
        'en': 'Click to buy more AI calls',
        'fr': "Cliquez pour acheter plus d'appels IA",
        'es': 'Haga clic para comprar más llamadas de IA',
        'ro': 'Faceți clic pentru a cumpăra mai multe apeluri IA',
    },
    'ai-instructions': {
        'en': 'AI instructions',
        'fr': 'Instructions IA',
        'es': 'Instrucciones IA',
        'ro': 'Instrucţiuni IA',
    },
    'ai-instructions-help': {
        'en': 'Please give here the instructions to the AI in order to generate the apropriate features needed',
        'fr': 'Veuillez donner ici les instructions à l\'IA afin de générer les fonctionnalités appropriées nécessaires',
        'es': 'Por favor, dé aquí las instrucciones a la IA para generar las características apropiadas necesarias',
        'ro': 'Vă rugăm să daţi aici instrucţiunile IA-ului pentru a genera funcţionalităţile apropiate necesare',
    },
    # Documentation chapters
    'chapter-1-intro': {
        'en': '1. Introduction to the Generator',
        'fr': '1. Introduction au Générateur',
        'es': '1. Introducción al Generador',
        'ro': '1. Introducere în Generator',
    },
    'what-is-generator': {
        'en': 'What is the Application Generator?',
        'fr': 'Qu\'est-ce que le Générateur d\'Applications ?',
        'es': '¿Qué es el Generador de Aplicaciones?',
        'ro': 'Ce este Generatorul de Aplicații?',
    },
    'generator-description': {
        'en': 'The Migratis Application Generator is a powerful AI-powered tool that helps you design, prototype, and generate full-stack web applications. It guides you through the entire development process, from concept to deployment.',
        'fr': 'Le Générateur d\'Applications Migratis est un outil puissant alimenté par l\'IA qui vous aide à concevoir, prototyper et générer des applications web full-stack. Il vous guide tout au long du processus de développement, du concept au déploiement.',
        'es': 'El Generador de Aplicaciones Migratis es una potente herramienta impulsada por IA que le ayuda a diseñar, prototipar y generar aplicaciones web full-stack. Le guía a través de todo el proceso de desarrollo, desde el concepto hasta el despliegue.',
        'ro': 'Generatorul de Aplicații Migratis este un instrument puternic alimentat de IA care vă ajută să proiectați, prototipați și generați aplicații web full-stack. Vă ghidează prin întregul proces de dezvoltare, de la concept la implementare.',
    },
    'key-features': {
        'en': 'Key Features',
        'fr': 'Fonctionnalités Clés',
        'es': 'Características Clave',
        'ro': 'Funcționalități Cheie',
    },
    'feature-ai-powered': {
        'en': 'AI-powered schema design and code generation',
        'fr': 'Conception de schéma et génération de code alimentées par l\'IA',
        'es': 'Diseño de esquemas y generación de código impulsados por IA',
        'ro': 'Proiectare scheme și generare cod alimentate de IA',
    },
    'feature-customizable': {
        'en': 'Fully customizable entities, fields, and relationships',
        'fr': 'Entités, champs et relations entièrement personnalisables',
        'es': 'Entidades, campos y relaciones totalmente personalizables',
        'ro': 'Entități, câmpuri și relații complet personalizabile',
    },
    'feature-sandbox-testing': {
        'en': 'Interactive sandbox for testing your data model',
        'fr': 'Bac à sable interactif pour tester votre modèle de données',
        'es': 'Sandbox interactivo para probar su modelo de datos',
        'ro': 'Sandbox interactiv pentru testarea modelului de date',
    },
    'feature-code-generation': {
        'en': 'One-click code generation for Django backend and React frontend',
        'fr': 'Génération de code en un clic pour le backend Django et le frontend React',
        'es': 'Generación de código con un clic para backend Django y frontend React',
        'ro': 'Generare cod cu un clic pentru backend Django și frontend React',
    },
    'feature-version-control': {
        'en': 'GitHub integration for version control and deployment',
        'fr': 'Intégration GitHub pour le contrôle de version et le déploiement',
        'es': 'Integración con GitHub para control de versiones y despliegue',
        'ro': 'Integrare GitHub pentru controlul versiunilor și implementare',
    },
    'chapter-2-create-app': {
        'en': '2. Create Your Application',
        'fr': '2. Créez Votre Application',
        'es': '2. Cree Su Aplicación',
        'ro': '2. Creați Aplicația Dvs.',
    },
    'step-1-create-application': {
        'en': 'Step 1: Create Application',
        'fr': 'Étape 1 : Créer une Application',
        'es': 'Paso 1: Crear Aplicación',
        'ro': 'Pasul 1: Creare Aplicație',
    },
    'step-1-1': {
        'en': 'Navigate to Applications in the left menu',
        'fr': 'Naviguez vers Applications dans le menu de gauche',
        'es': 'Navegue a Aplicaciones en el menú izquierdo',
        'ro': 'Navigați la Aplicații în meniul din stânga',
    },
    'step-1-2': {
        'en': 'Click the "Add application" button',
        'fr': 'Cliquez sur le bouton "Ajouter une application"',
        'es': 'Haga clic en el botón "Agregar aplicación"',
        'ro': 'Faceți clic pe butonul "Adaugă aplicație"',
    },
    'step-1-3': {
        'en': 'Fill in the application name and description',
        'fr': 'Remplissez le nom et la description de l\'application',
        'es': 'Complete el nombre y la descripción de la aplicación',
        'ro': 'Completați numele și descrierea aplicației',
    },
    'step-1-4': {
        'en': 'Select the modules you need (User, Subscription, i18n, etc.)',
        'fr': 'Sélectionnez les modules dont vous avez besoin (Utilisateur, Abonnement, i18n, etc.)',
        'es': 'Seleccione los módulos que necesita (Usuario, Suscripción, i18n, etc.)',
        'ro': 'Selectați modulele de care aveți nevoie (Utilizator, Abonament, i18n, etc.)',
    },
    'application-status': {
        'en': 'Application Status',
        'fr': 'Statut de l\'Application',
        'es': 'Estado de la Aplicación',
        'ro': 'Starea Aplicației',
    },
    'status-draft': {
        'en': 'Draft',
        'fr': 'Brouillon',
        'es': 'Borrador',
        'ro': 'Ciornă',
    },
    'status-draft-desc': {
        'en': 'Initial state - you can still modify the schema',
        'fr': 'État initial - vous pouvez toujours modifier le schéma',
        'es': 'Estado inicial - aún puede modificar el esquema',
        'ro': 'Stare inițială - încă puteți modifica schema',
    },
    'status-ongoing': {
        'en': 'Ongoing',
        'fr': 'En cours',
        'es': 'En curso',
        'ro': 'În desfășurare',
    },
    'status-ongoing-desc': {
        'en': 'AI is analyzing your application',
        'fr': 'L\'IA analyse votre application',
        'es': 'La IA está analizando su aplicación',
        'ro': 'IA analizează aplicația dvs.',
    },
    'status-generated': {
        'en': 'Generated',
        'fr': 'Généré',
        'es': 'Generado',
        'ro': 'Generat',
    },
    'status-generated-desc': {
        'en': 'Code has been generated and is ready for export',
        'fr': 'Le code a été généré et est prêt pour l\'export',
        'es': 'El código ha sido generado y está listo para exportar',
        'ro': 'Codul a fost generat și este gata de export',
    },
    'modules': {
        'en': 'Modules',
        'fr': 'Modules',
        'es': 'Módulos',
        'ro': 'Module',
    },
    'modules-description': {
        'en': 'Modules add pre-built functionality to your application',
        'fr': 'Les modules ajoutent des fonctionnalités pré-construites à votre application',
        'es': 'Los módulos agregan funcionalidad pre-construida a su aplicación',
        'ro': 'Modulele adaugă funcționalități pre-construite aplicației dvs.',
    },
    'module-user': {
        'en': 'User Management',
        'fr': 'Gestion des Utilisateurs',
        'es': 'Gestión de Usuarios',
        'ro': 'Gestiune Utilizatori',
    },
    'module-user-desc': {
        'en': 'Authentication, registration, and user profiles',
        'fr': 'Authentification, inscription et profils utilisateurs',
        'es': 'Autenticación, registro y perfiles de usuario',
        'ro': 'Autentificare, înregistrare și profiluri utilizator',
    },
    'module-subscription': {
        'en': 'Subscription Management',
        'fr': 'Gestion des Abonnements',
        'es': 'Gestión de Suscripciones',
        'ro': 'Gestiune Abonamente',
    },
    'module-subscription-desc': {
        'en': 'Stripe integration for paid plans and subscriptions',
        'fr': 'Intégration Stripe pour les plans payants et abonnements',
        'es': 'Integración con Stripe para planes de pago y suscripciones',
        'ro': 'Integrare Stripe pentru planuri plătite și abonamente',
    },
    'module-i18n': {
        'en': 'Internationalization (i18n)',
        'fr': 'Internationalisation (i18n)',
        'es': 'Internacionalización (i18n)',
        'ro': 'Internalizare (i18n)',
    },
    'module-i18n-desc': {
        'en': 'Multi-language support for your application',
        'fr': 'Support multi-langues pour votre application',
        'es': 'Soporte multi-idioma para su aplicación',
        'ro': 'Suport multi-limbă pentru aplicația dvs.',
    },
    'module-support': {
        'en': 'Support System',
        'fr': 'Système de Support',
        'es': 'Sistema de Soporte',
        'ro': 'Sistem de Suport',
    },
    'module-support-desc': {
        'en': 'Help tickets and customer support',
        'fr': 'Tickets d\'aide et support client',
        'es': 'Tickets de ayuda y atención al cliente',
        'ro': 'Tickete de ajutor și suport pentru clienți',
    },
    'module-cookie': {
        'en': 'Cookie Consent',
        'fr': 'Consentement aux Cookies',
        'es': 'Consentimiento de Cookies',
        'ro': 'Consimțământ Cookie',
    },
    'module-cookie-desc': {
        'en': 'GDPR-compliant cookie consent banner',
        'fr': 'Bannière de consentement aux cookies conforme au RGPD',
        'es': 'Banner de consentimiento de cookies conforme al RGPD',
        'ro': 'Banner de consimțământ cookie conform GDPR',
    },
    'ai-analysis-after-validation': {
        'en': 'AI Analysis After Validation',
        'fr': 'Analyse IA Après Validation',
        'es': 'Análisis de IA Después de la Validación',
        'ro': 'Analiză IA După Validare',
    },
    'ai-analysis-after-validation-desc': {
        'en': 'Once your application is validated, a sparkle icon appears on the application card. Click it to run AI analysis which analyzes your application description and generates the initial schema.',
        'fr': 'Une fois votre application validée, une icône étincelle apparaît sur la carte de l\'application. Cliquez dessus pour lancer l\'analyse IA qui analyse la description de votre application et génère le schéma initial.',
        'es': 'Una vez que su aplicación está validada, aparece un icono de destello en la tarjeta de la aplicación. Haga clic para ejecutar el análisis de IA que analiza la descripción de su aplicación y genera el esquema inicial.',
        'ro': 'Odată ce aplicația dvs. este validată, o pictogramă de scânteie apare pe cartela aplicației. Faceți clic pentru a rula analiza IA care analizează descrierea aplicației și generează schema inițială.',
    },
    'chapter-3-review-schema': {
        'en': '3. Review and Update the Generated Schema',
        'fr': '3. Examiner et Mettre à Jour le Schéma Généré',
        'es': '3. Revisar y Actualizar el Esquema Generado',
        'ro': '3. Revizuiți și Actualizați Schema Generată',
    },
    'review-schema-intro': {
        'en': 'After AI analysis, review and refine your schema',
        'fr': 'Après l\'analyse IA, examinez et affinez votre schéma',
        'es': 'Después del análisis de IA, revise y refine su esquema',
        'ro': 'După analiza IA, revizuiți și rafinați schema',
    },
    'review-schema-intro-desc': {
        'en': 'The AI generates an initial schema based on your application description. Now you can review, modify, and enhance it by adding entities, fields, and relationships.',
        'fr': 'L\'IA génère un schéma initial basé sur la description de votre application. Vous pouvez maintenant l\'examiner, le modifier et l\'améliorer en ajoutant des entités, des champs et des relations.',
        'es': 'La IA genera un esquema inicial basado en la descripción de su aplicación. Ahora puede revisarlo, modificarlo y mejorarlo agregando entidades, campos y relaciones.',
        'ro': 'IA generează o schemă inițială bazată pe descrierea aplicației dvs. Acum o puteți examina, modifica și îmbunătăți adăugând entități, câmpuri și relații.',
    },
    'chapter-4-sandbox': {
        'en': '4. Sandbox Testing',
        'fr': '4. Test Bac à Sable',
        'es': '4. Pruebas en Sandbox',
        'ro': '4. Testare Sandbox',
    },
    'chapter-5-code-gen': {
        'en': '5. Code Generation',
        'fr': '5. Génération de Code',
        'es': '5. Generación de Código',
        'ro': '5. Generare Cod',
    },
    'chapter-6-github': {
        'en': '6. GitHub Integration',
        'fr': '6. Intégration GitHub',
        'es': '6. Integración con GitHub',
        'ro': '6. Integrare GitHub',
    },
    'chapter-7-best-practices': {
        'en': '7. Best Practices',
        'fr': '7. Meilleures Pratiques',
        'es': '7. Mejores Prácticas',
        'ro': '7. Cele Mai Bune Practici',
    },
    'chapter-3-design-entities': {
        'en': '3. Design Your Entities',
        'fr': '3. Concevez Vos Entités',
        'es': '3. Diseñe Sus Entidades',
        'ro': '3. Proiectați Entitățile Dvs.',
    },
    'step-2-create-entities': {
        'en': 'Step 2: Create Entities',
        'fr': 'Étape 2 : Créer des Entités',
        'es': 'Paso 2: Crear Entidades',
        'ro': 'Pasul 2: Creare Entități',
    },
    'step-2-1': {
        'en': 'Select your application from the dropdown',
        'fr': 'Sélectionnez votre application dans la liste déroulante',
        'es': 'Seleccione su aplicación de la lista desplegable',
        'ro': 'Selectați aplicația dvs. din lista derulantă',
    },
    'step-2-2': {
        'en': 'Click "Add entity" and define the entity name and role',
        'fr': 'Cliquez sur "Ajouter une entité" et définissez le nom et le rôle de l\'entité',
        'es': 'Haga clic en "Agregar entidad" y defina el nombre y rol de la entidad',
        'ro': 'Faceți clic pe "Adaugă entitate" și definiți numele și rolul entității',
    },
    'step-2-3': {
        'en': 'Add AI instructions to guide the code generation',
        'fr': 'Ajoutez des instructions IA pour guider la génération de code',
        'es': 'Agregue instrucciones de IA para guiar la generación de código',
        'ro': 'Adăugați instrucțiuni IA pentru a ghida generarea codului',
    },
    'entity-roles': {
        'en': 'Entity Roles',
        'fr': 'Rôles des Entités',
        'es': 'Roles de Entidad',
        'ro': 'Roluri Entitate',
    },
    'role-model': {
        'en': 'Model',
        'fr': 'Modèle',
        'es': 'Modelo',
        'ro': 'Model',
    },
    'role-model-desc': {
        'en': 'Database model with persistence',
        'fr': 'Modèle de base de données avec persistance',
        'es': 'Modelo de base de datos con persistencia',
        'ro': 'Model de bază de date cu persistență',
    },
    'role-service': {
        'en': 'Service',
        'fr': 'Service',
        'es': 'Servicio',
        'ro': 'Serviciu',
    },
    'role-service-desc': {
        'en': 'Business logic layer',
        'fr': 'Couche de logique métier',
        'es': 'Capa de lógica de negocio',
        'ro': 'Strat de logică de afaceri',
    },
    'role-controller': {
        'en': 'Controller',
        'fr': 'Contrôleur',
        'es': 'Controlador',
        'ro': 'Controler',
    },
    'role-controller-desc': {
        'en': 'API endpoint handler',
        'fr': 'Gestionnaire de point de terminaison API',
        'es': 'Manejador de endpoint de API',
        'ro': 'Handler de punct final API',
    },
    'role-utility': {
        'en': 'Utility',
        'fr': 'Utilitaire',
        'es': 'Utilidad',
        'ro': 'Utilitar',
    },
    'role-utility-desc': {
        'en': 'Helper functions and utilities',
        'fr': 'Fonctions utilitaires et aides',
        'es': 'Funciones auxiliares y utilidades',
        'ro': 'Funcții auxiliare și utilități',
    },
    'ai-instructions-description': {
        'en': 'AI instructions guide the code generator on how to implement the entity. Be specific about validation rules, business logic, and UI requirements.',
        'fr': 'Les instructions IA guident le générateur de code sur la façon d\'implémenter l\'entité. Soyez précis sur les règles de validation, la logique métier et les exigences d\'interface utilisateur.',
        'es': 'Las instrucciones de IA guían al generador de código sobre cómo implementar la entidad. Sea específico sobre las reglas de validación, la lógica de negocio y los requisitos de UI.',
        'ro': 'Instrucțiunile IA ghidează generatorul de cod despre cum să implementeze entitatea. Fiți specific despre regulile de validare, logica de afaceri și cerințele de interfață.',
    },
    'ai-instructions-tip': {
        'en': 'Example: "This field should be a unique email address with validation. Display as a text input with email format checking."',
        'fr': 'Exemple : "Ce champ doit être une adresse email unique avec validation. Afficher comme un champ texte avec vérification du format email."',
        'es': 'Ejemplo: "Este campo debe ser una dirección de correo electrónico única con validación. Mostrar como un campo de texto con verificación de formato de correo electrónico."',
        'ro': 'Exemplu: "Acest câmp trebuie să fie o adresă de email unică cu validare. Afișează ca un câmp text cu verificare format email."',
    },
    'tip': {
        'en': 'Tip',
        'fr': 'Astuce',
        'es': 'Consejo',
        'ro': 'Sfat',
    },
    'chapter-4-define-fields': {
        'en': '4. Define Fields',
        'fr': '4. Définir les Champs',
        'es': '4. Definir Campos',
        'ro': '4. Definire Câmpuri',
    },
    'step-3-create-fields': {
        'en': 'Step 3: Create Fields',
        'fr': 'Étape 3 : Créer des Champs',
        'es': 'Paso 3: Crear Campos',
        'ro': 'Pasul 3: Creare Câmpuri',
    },
    'step-3-1': {
        'en': 'Select your entity from the dropdown',
        'fr': 'Sélectionnez votre entité dans la liste déroulante',
        'es': 'Seleccione su entidad de la lista desplegable',
        'ro': 'Selectați entitatea dvs. din lista derulantă',
    },
    'step-3-2': {
        'en': 'Click "Add field" and choose the field type',
        'fr': 'Cliquez sur "Ajouter un champ" et choisissez le type de champ',
        'es': 'Haga clic en "Agregar campo" y elija el tipo de campo',
        'ro': 'Faceți clic pe "Adaugă câmp" și alegeți tipul de câmp',
    },
    'step-3-3': {
        'en': 'Set required flag and add AI instructions if needed',
        'fr': 'Définissez l\'indicateur requis et ajoutez des instructions IA si nécessaire',
        'es': 'Establezca la marca de requerido y agregue instrucciones de IA si es necesario',
        'ro': 'Setați indicatorul de obligatoriu și adăugați instrucțiuni IA dacă este necesar',
    },
    'field-types': {
        'en': 'Field Types',
        'fr': 'Types de Champs',
        'es': 'Tipos de Campos',
        'ro': 'Tipuri de Câmpuri',
    },
    'type-string': {
        'en': 'String',
        'fr': 'Chaîne',
        'es': 'Cadena',
        'ro': 'Șir',
    },
    'type-string-desc': {
        'en': 'Short text (up to 255 characters)',
        'fr': 'Texte court (jusqu\'à 255 caractères)',
        'es': 'Texto corto (hasta 255 caracteres)',
        'ro': 'Text scurt (până la 255 de caractere)',
    },
    'type-text': {
        'en': 'Text',
        'fr': 'Texte',
        'es': 'Texto',
        'ro': 'Text',
    },
    'type-text-desc': {
        'en': 'Long text (unlimited length)',
        'fr': 'Texte long (longueur illimitée)',
        'es': 'Texto largo (longitud ilimitada)',
        'ro': 'Text lung (lungime nelimitată)',
    },
    'type-integer': {
        'en': 'Integer',
        'fr': 'Entier',
        'es': 'Entero',
        'ro': 'Întreg',
    },
    'type-integer-desc': {
        'en': 'Whole numbers',
        'fr': 'Nombres entiers',
        'es': 'Números enteros',
        'ro': 'Numere întregi',
    },
    'type-decimal': {
        'en': 'Decimal',
        'fr': 'Décimal',
        'es': 'Decimal',
        'ro': 'Zecimal',
    },
    'type-decimal-desc': {
        'en': 'Numbers with decimal points',
        'fr': 'Nombres avec virgule',
        'es': 'Números con decimales',
        'ro': 'Numere cu zecimale',
    },
    'type-boolean': {
        'en': 'Boolean',
        'fr': 'Booléen',
        'es': 'Booleano',
        'ro': 'Boolean',
    },
    'type-boolean-desc': {
        'en': 'True/False values',
        'fr': 'Vrais/Faux valeurs',
        'es': 'Valores Verdadero/Falso',
        'ro': 'Valori Adevărat/Fals',
    },
    'type-date': {
        'en': 'Date',
        'fr': 'Date',
        'es': 'Fecha',
        'ro': 'Dată',
    },
    'type-date-desc': {
        'en': 'Date without time',
        'fr': 'Date sans heure',
        'es': 'Fecha sin hora',
        'ro': 'Dată fără oră',
    },
    'type-datetime': {
        'en': 'DateTime',
        'fr': 'Date et Heure',
        'es': 'Fecha y Hora',
        'ro': 'Dată și Oră',
    },
    'type-datetime-desc': {
        'en': 'Date with time',
        'fr': 'Date avec heure',
        'es': 'Fecha con hora',
        'ro': 'Dată cu oră',
    },
    'type-file': {
        'en': 'File',
        'fr': 'Fichier',
        'es': 'Archivo',
        'ro': 'Fișier',
    },
    'type-file-desc': {
        'en': 'File upload',
        'fr': 'Téléchargement de fichier',
        'es': 'Carga de archivos',
        'ro': 'Încărcare fișier',
    },
    'type-fk': {
        'en': 'Foreign Key',
        'fr': 'Clé Étrangère',
        'es': 'Clave Foránea',
        'ro': 'Cheie Străină',
    },
    'type-fk-desc': {
        'en': 'One-to-one or one-to-many relationship',
        'fr': 'Relation un-à-un ou un-à-plusieurs',
        'es': 'Relación uno-a-uno o uno-a-muchos',
        'ro': 'Relație unu-la-unu sau unu-la-mai-mulți',
    },
    'type-m2m': {
        'en': 'Many-to-Many',
        'fr': 'Plusieurs-à-Plusieurs',
        'es': 'Muchos-a-Muchos',
        'ro': 'Mai-mulți-la-Mai-mulți',
    },
    'type-m2m-desc': {
        'en': 'Many-to-many relationship',
        'fr': 'Relation plusieurs-à-plusieurs',
        'es': 'Relación muchos-a-muchos',
        'ro': 'Relație mai-mulți-la-mai-mulți',
    },
    'field-options': {
        'en': 'Field Options',
        'fr': 'Options de Champ',
        'es': 'Opciones de Campo',
        'ro': 'Opțiuni Câmp',
    },
    'option-required': {
        'en': 'Required',
        'fr': 'Obligatoire',
        'es': 'Requerido',
        'ro': 'Obligatoriu',
    },
    'option-required-desc': {
        'en': 'Field must have a value',
        'fr': 'Le champ doit avoir une valeur',
        'es': 'El campo debe tener un valor',
        'ro': 'Câmpul trebuie să aibă o valoare',
    },
    'option-ai-instructions': {
        'en': 'AI Instructions',
        'fr': 'Instructions IA',
        'es': 'Instrucciones de IA',
        'ro': 'Instrucțiuni IA',
    },
    'option-ai-instructions-desc': {
        'en': 'Guide the AI on how to handle this field',
        'fr': 'Guider l\'IA sur la façon de gérer ce champ',
        'es': 'Guíe a la IA sobre cómo manejar este campo',
        'ro': 'Ghidați IA despre cum să gestioneze acest câmp',
    },
    'chapter-5-relationships': {
        'en': '5. Create Relationships',
        'fr': '5. Créer des Relations',
        'es': '5. Crear Relaciones',
        'ro': '5. Creare Relații',
    },
    'step-4-create-relationships': {
        'en': 'Step 4: Create Relationships',
        'fr': 'Étape 4 : Créer des Relations',
        'es': 'Paso 4: Crear Relaciones',
        'ro': 'Pasul 4: Creare Relații',
    },
    'step-4-1': {
        'en': 'Relationships are created automatically when you add FK or M2M fields',
        'fr': 'Les relations sont créées automatiquement lorsque vous ajoutez des champs FK ou M2M',
        'es': 'Las relaciones se crean automáticamente cuando agrega campos FK o M2M',
        'ro': 'Relațiile sunt create automat când adăugați câmpuri FK sau M2M',
    },
    'step-4-2': {
        'en': 'Review relationships in the entity view to ensure correct direction',
        'fr': 'Vérifiez les relations dans la vue des entités pour vous assurer de la direction correcte',
        'es': 'Revise las relaciones en la vista de entidad para asegurar la dirección correcta',
        'ro': 'Revizuiți relațiile în vizualizarea entității pentru a asigura direcția corectă',
    },
    'relationship-types': {
        'en': 'Relationship Types',
        'fr': 'Types de Relations',
        'es': 'Tipos de Relaciones',
        'ro': 'Tipuri de Relații',
    },
    'rel-one-to-one': {
        'en': 'One-to-One',
        'fr': 'Un-à-Un',
        'es': 'Uno-a-Uno',
        'ro': 'Unu-la-Unu',
    },
    'rel-one-to-one-desc': {
        'en': 'One record relates to exactly one other record',
        'fr': 'Un enregistrement se rapporte à exactement un autre enregistrement',
        'es': 'Un registro se relaciona con exactamente otro registro',
        'ro': 'O înregistrare se referă la exact o altă înregistrare',
    },
    'rel-one-to-many': {
        'en': 'One-to-Many',
        'fr': 'Un-à-Plusieurs',
        'es': 'Uno-a-Muchos',
        'ro': 'Unu-la-Mai-mulți',
    },
    'rel-one-to-many-desc': {
        'en': 'One record relates to many other records',
        'fr': 'Un enregistrement se rapporte à plusieurs autres enregistrements',
        'es': 'Un registro se relaciona con muchos otros registros',
        'ro': 'O înregistrare se referă la mai multe alte înregistrări',
    },
    'rel-many-to-many': {
        'en': 'Many-to-Many',
        'fr': 'Plusieurs-à-Plusieurs',
        'es': 'Muchos-a-Muchos',
        'ro': 'Mai-mulți-la-Mai-mulți',
    },
    'rel-many-to-many-desc': {
        'en': 'Many records relate to many other records',
        'fr': 'Plusieurs enregistrements se rapportent à plusieurs autres enregistrements',
        'es': 'Muchos registros se relacionan con muchos otros registros',
        'ro': 'Mai multe înregistrări se referă la mai multe alte înregistrări',
    },
    'important': {
        'en': 'Important',
        'fr': 'Important',
        'es': 'Importante',
        'ro': 'Important',
    },
    'rel-direction-warning': {
        'en': 'For one-to-many relationships, the FK must be on the "many" side. Example: For "Client has many Invoices", the FK should be on Invoice (Invoice.client), not on Client.',
        'fr': 'Pour les relations un-à-plusieurs, la FK doit être du côté "plusieurs". Exemple : Pour "Client a plusieurs Factures", la FK doit être sur Facture (Facture.client), pas sur Client.',
        'es': 'Para relaciones uno-a-muchos, la FK debe estar en el lado "muchos". Ejemplo: Para "Cliente tiene muchas Facturas", la FK debe estar en Factura (Factura.cliente), no en Cliente.',
        'ro': 'Pentru relațiile unu-la-mai-mulți, FK trebuie să fie în partea "mai-mulți". Exemplu: Pentru "Client are multe Facturi", FK trebuie să fie pe Factură (Factură.client), nu pe Client.',
    },
    'chapter-6-ai-analysis': {
        'en': '6. AI Analysis',
        'fr': '6. Analyse IA',
        'es': '6. Análisis de IA',
        'ro': '6. Analiză IA',
    },
    'step-5-ai-analysis': {
        'en': 'Step 5: AI Analysis',
        'fr': 'Étape 5 : Analyse IA',
        'es': 'Paso 5: Análisis de IA',
        'ro': 'Pasul 5: Analiză IA',
    },
    'ai-analysis-description': {
        'en': 'AI analysis optimizes your schema and generates rendering configurations for the sandbox.',
        'fr': 'L\'analyse IA optimise votre schéma et génère des configurations de rendu pour le bac à sable.',
        'es': 'El análisis de IA optimiza su esquema y genera configuraciones de renderizado para el sandbox.',
        'ro': 'Analiza IA optimizează schema dvs. și generează configurații de redare pentru sandbox.',
    },
    'step-5-1': {
        'en': 'Click the sparkle icon on an application card',
        'fr': 'Cliquez sur l\'icône étincelle sur une carte d\'application',
        'es': 'Haga clic en el icono de destello en una tarjeta de aplicación',
        'ro': 'Faceți clic pe pictograma de scânteie pe o cartelă de aplicație',
    },
    'step-5-2': {
        'en': 'Confirm the AI analysis (uses AI credits)',
        'fr': 'Confirmez l\'analyse IA (utilise des crédits IA)',
        'es': 'Confirme el análisis de IA (usa créditos de IA)',
        'ro': 'Confirmați analiza IA (folosește credite IA)',
    },
    'step-5-3': {
        'en': 'Wait for the AI to complete the analysis',
        'fr': 'Attendez que l\'IA termine l\'analyse',
        'es': 'Espere a que la IA complete el análisis',
        'ro': 'Așteptați ca IA să completeze analiza',
    },
    'ai-usage': {
        'en': 'AI Usage',
        'fr': 'Utilisation IA',
        'es': 'Uso de IA',
        'ro': 'Utilizare IA',
    },
    'ai-usage-description': {
        'en': 'AI calls are used for schema analysis and code generation',
        'fr': 'Les appels IA sont utilisés pour l\'analyse de schéma et la génération de code',
        'es': 'Las llamadas de IA se usan para análisis de esquema y generación de código',
        'ro': 'Apelurile IA sunt utilizate pentru analiza schemei și generarea codului',
    },
    'ai-usage-1': {
        'en': 'Free tier includes 10 AI calls (one-time allocation)',
        'fr': 'Le niveau gratuit comprend 10 appels IA (allocation unique)',
        'es': 'El nivel gratuito incluye 10 llamadas de IA (asignación única)',
        'ro': 'Nivelul gratuit include 10 apeluri IA (alocare unică)',
    },
    'ai-usage-2': {
        'en': 'Additional calls can be purchased',
        'fr': 'Des appels supplémentaires peuvent être achetés',
        'es': 'Se pueden comprar llamadas adicionales',
        'ro': 'Apelurile suplimentare pot fi achiziționate',
    },
    'ai-usage-3': {
        'en': 'Usage is tracked in your account',
        'fr': 'L\'utilisation est suivie dans votre compte',
        'es': 'El uso se rastrea en su cuenta',
        'ro': 'Utilizarea este urmărită în contul dvs.',
    },
    'ai-usage-tip': {
        'en': 'Use AI refresh wisely in the sandbox - it\'s most valuable after you\'ve made significant changes to your schema',
        'fr': 'Utilisez le rafraîchissement IA sagement dans le bac à sable - il est plus précieux après avoir apporté des modifications importantes à votre schéma',
        'es': 'Use la actualización de IA sabiamente en el sandbox - es más valiosa después de haber realizado cambios significativos en su esquema',
        'ro': 'Utilizați reîmprospătarea IA cu înțelepciune în sandbox - este cea mai valoroasă după ce ați făcut modificări semnificative în schema',
    },
    'chapter-7-sandbox': {
        'en': '7. Sandbox Testing',
        'fr': '7. Test Bac à Sable',
        'es': '7. Pruebas en Sandbox',
        'ro': '7. Testare Sandbox',
    },
    'step-6-sandbox-testing': {
        'en': 'Step 6: Sandbox Testing',
        'fr': 'Étape 6 : Test Bac à Sable',
        'es': 'Paso 6: Pruebas en Sandbox',
        'ro': 'Pasul 6: Testare Sandbox',
    },
    'sandbox-description': {
        'en': 'The sandbox is a live testing environment for your data model',
        'fr': 'Le bac à sable est un environnement de test en direct pour votre modèle de données',
        'es': 'El sandbox es un entorno de prueba en vivo para su modelo de datos',
        'ro': 'Sandbox-ul este un mediu de testare în direct pentru modelul dvs. de date',
    },
    'step-6-1': {
        'en': 'Click the flask icon on an application card',
        'fr': 'Cliquez sur l\'icône fiole sur une carte d\'application',
        'es': 'Haga clic en el icono de matraz en una tarjeta de aplicación',
        'ro': 'Faceți clic pe pictograma de balon pe o cartelă de aplicație',
    },
    'step-6-2': {
        'en': 'Choose AI refresh or default refresh',
        'fr': 'Choisissez rafraîchissement IA ou rafraîchissement par défaut',
        'es': 'Elija actualización de IA o actualización predeterminada',
        'ro': 'Alegeți reîmprospătare IA sau reîmprospătare implicită',
    },
    'step-6-3': {
        'en': 'Create, edit, and delete test records',
        'fr': 'Créez, modifiez et supprimez des enregistrements de test',
        'es': 'Cree, edite y elimine registros de prueba',
        'ro': 'Creați, editați și ștergeți înregistrări de test',
    },
    'step-6-4': {
        'en': 'Use search and filters to find records',
        'fr': 'Utilisez la recherche et les filtres pour trouver des enregistrements',
        'es': 'Use búsqueda y filtros para encontrar registros',
        'ro': 'Folosiți căutarea și filtrele pentru a găsi înregistrări',
    },
    'sandbox-features': {
        'en': 'Sandbox Features',
        'fr': 'Fonctionnalités du Bac à Sable',
        'es': 'Características del Sandbox',
        'ro': 'Funcționalități Sandbox',
    },
    'sandbox-search': {
        'en': 'Search',
        'fr': 'Recherche',
        'es': 'Búsqueda',
        'ro': 'Căutare',
    },
    'sandbox-search-desc': {
        'en': 'Full-text search across searchable fields',
        'fr': 'Recherche en texte intégral dans les champs consultables',
        'es': 'Búsqueda de texto completo en campos consultables',
        'ro': 'Căutare full-text în câmpurile consultabile',
    },
    'sandbox-filters': {
        'en': 'Filters',
        'fr': 'Filtres',
        'es': 'Filtros',
        'ro': 'Filtre',
    },
    'sandbox-filters-desc': {
        'en': 'Filter records by field values',
        'fr': 'Filtrer les enregistrements par valeurs de champ',
        'es': 'Filtrar registros por valores de campo',
        'ro': 'Filtrează înregistrările după valorile câmpului',
    },
    'sandbox-sort': {
        'en': 'Sorting',
        'fr': 'Tri',
        'es': 'Ordenación',
        'ro': 'Sortare',
    },
    'sandbox-sort-desc': {
        'en': 'Sort records by any field',
        'fr': 'Trier les enregistrements par n\'importe quel champ',
        'es': 'Ordenar registros por cualquier campo',
        'ro': 'Sortează înregistrările după orice câmp',
    },
    'sandbox-pagination': {
        'en': 'Pagination',
        'fr': 'Pagination',
        'es': 'Paginación',
        'ro': 'Paginare',
    },
    'sandbox-pagination-desc': {
        'en': 'Navigate through large datasets',
        'fr': 'Naviguer dans les grands ensembles de données',
        'es': 'Navegar a través de grandes conjuntos de datos',
        'ro': 'Navigați prin seturi mari de date',
    },
    'sandbox-ai-refresh': {
        'en': 'AI Refresh',
        'fr': 'Rafraîchissement IA',
        'es': 'Actualización de IA',
        'ro': 'Reîmprospătare IA',
    },
    'sandbox-ai-refresh-desc': {
        'en': 'Regenerate sandbox configuration with AI',
        'fr': 'Régénérer la configuration du bac à sable avec l\'IA',
        'es': 'Regenerar configuración de sandbox con IA',
        'ro': 'Regenerați configurația sandbox cu IA',
    },
    'sandbox-tip': {
        'en': 'The sandbox is free and unlimited - use it to thoroughly test your data model before generating code',
        'fr': 'Le bac à sable est gratuit et illimité - utilisez-le pour tester soigneusement votre modèle de données avant de générer du code',
        'es': 'El sandbox es gratuito e ilimitado - úselo para probar a fondo su modelo de datos antes de generar código',
        'ro': 'Sandbox-ul este gratuit și nelimitat - folosiți-l pentru a testa temeinic modelul de date înainte de a genera cod',
    },
    'chapter-8-code-gen': {
        'en': '8. Code Generation',
        'fr': '8. Génération de Code',
        'es': '8. Generación de Código',
        'ro': '8. Generare Cod',
    },
    'step-7-code-generation': {
        'en': 'Step 7: Code Generation',
        'fr': 'Étape 7 : Génération de Code',
        'es': 'Paso 7: Generación de Código',
        'ro': 'Pasul 7: Generare Cod',
    },
    'code-gen-description': {
        'en': 'Generate production-ready code for your application',
        'fr': 'Générer du code prêt pour la production pour votre application',
        'es': 'Generar código listo para producción para su aplicación',
        'ro': 'Generați cod gata de producție pentru aplicația dvs.',
    },
    'step-7-1': {
        'en': 'Ensure your schema is complete and tested',
        'fr': 'Assurez-vous que votre schéma est complet et testé',
        'es': 'Asegúrese de que su esquema esté completo y probado',
        'ro': 'Asigurați-vă că schema dvs. este completă și testată',
    },
    'step-7-2': {
        'en': 'Click the code generation button',
        'fr': 'Cliquez sur le bouton de génération de code',
        'es': 'Haga clic en el botón de generación de código',
        'ro': 'Faceți clic pe butonul de generare cod',
    },
    'step-7-3': {
        'en': 'Download or push to GitHub',
        'fr': 'Télécharger ou pousser vers GitHub',
        'es': 'Descargar o enviar a GitHub',
        'ro': 'Descărcați sau împingeți către GitHub',
    },
    'generated-code': {
        'en': 'Generated Code',
        'fr': 'Code Généré',
        'es': 'Código Generado',
        'ro': 'Cod Generat',
    },
    'code-backend': {
        'en': 'Backend',
        'fr': 'Backend',
        'es': 'Backend',
        'ro': 'Backend',
    },
    'code-backend-desc': {
        'en': 'Django models, views, and APIs',
        'fr': 'Modèles Django, vues et API',
        'es': 'Modelos Django, vistas y APIs',
        'ro': 'Modele Django, vizualizări și API-uri',
    },
    'code-frontend': {
        'en': 'Frontend',
        'fr': 'Frontend',
        'es': 'Frontend',
        'ro': 'Frontend',
    },
    'code-frontend-desc': {
        'en': 'React components and pages',
        'fr': 'Composants et pages React',
        'es': 'Componentes y páginas React',
        'ro': 'Componente și pagini React',
    },
    'code-models': {
        'en': 'Models',
        'fr': 'Modèles',
        'es': 'Modelos',
        'ro': 'Modele',
    },
    'code-models-desc': {
        'en': 'Database schema and relationships',
        'fr': 'Schéma de base de données et relations',
        'es': 'Esquema de base de datos y relaciones',
        'ro': 'Schema de bază de date și relații',
    },
    'code-apis': {
        'en': 'APIs',
        'fr': 'API',
        'es': 'APIs',
        'ro': 'API-uri',
    },
    'code-apis-desc': {
        'en': 'REST API endpoints with Ninja',
        'fr': 'Points de terminaison API REST avec Ninja',
        'es': 'Endpoints de API REST con Ninja',
        'ro': 'Puncte finale API REST cu Ninja',
    },
    'code-admin': {
        'en': 'Admin Interface',
        'fr': 'Interface d\'Administration',
        'es': 'Interfaz de Administración',
        'ro': 'Interfață de Administrare',
    },
    'code-admin-desc': {
        'en': 'Django admin configuration',
        'fr': 'Configuration de l\'admin Django',
        'es': 'Configuración de admin de Django',
        'ro': 'Configurare admin Django',
    },
    'code-gen-warning': {
        'en': 'Code generation requires a subscription. Make sure your schema is final before generating.',
        'fr': 'La génération de code nécessite un abonnement. Assurez-vous que votre schéma est final avant de générer.',
        'es': 'La generación de código requiere una suscripción. Asegúrese de que su esquema sea final antes de generar.',
        'ro': 'Generarea codului necesită un abonament. Asigurați-vă că schema dvs. este finală înainte de a genera.',
    },
    'chapter-9-github': {
        'en': '9. GitHub Integration',
        'fr': '9. Intégration GitHub',
        'es': '9. Integración con GitHub',
        'ro': '9. Integrare GitHub',
    },
    'step-8-github-integration': {
        'en': 'Step 8: GitHub Integration',
        'fr': 'Étape 8 : Intégration GitHub',
        'es': 'Paso 8: Integración con GitHub',
        'ro': 'Pasul 8: Integrare GitHub',
    },
    'github-description': {
        'en': 'Push your generated code directly to GitHub',
        'fr': 'Poussez votre code généré directement vers GitHub',
        'es': 'Empuje su código generado directamente a GitHub',
        'ro': 'Împingeți codul generat direct către GitHub',
    },
    'step-8-1': {
        'en': 'Connect your GitHub account in settings',
        'fr': 'Connectez votre compte GitHub dans les paramètres',
        'es': 'Conecte su cuenta de GitHub en configuración',
        'ro': 'Conectați contul GitHub în setări',
    },
    'step-8-2': {
        'en': 'Create or select a repository',
        'fr': 'Créer ou sélectionner un dépôt',
        'es': 'Crear o seleccionar un repositorio',
        'ro': 'Creați sau selectați un depozit',
    },
    'step-8-3': {
        'en': 'Push your code with one click',
        'fr': 'Poussez votre code en un clic',
        'es': 'Empuje su código con un clic',
        'ro': 'Împingeți codul cu un clic',
    },
    'github-benefits': {
        'en': 'GitHub Benefits',
        'fr': 'Avantages GitHub',
        'es': 'Beneficios de GitHub',
        'ro': 'Beneficii GitHub',
    },
    'github-benefit-1': {
        'en': 'Version control for your code',
        'fr': 'Contrôle de version pour votre code',
        'es': 'Control de versiones para su código',
        'ro': 'Controlul versiunilor pentru codul dvs.',
    },
    'github-benefit-2': {
        'en': 'Collaboration with team members',
        'fr': 'Collaboration avec les membres de l\'équipe',
        'es': 'Colaboración con miembros del equipo',
        'ro': 'Colaborare cu membrii echipei',
    },
    'github-benefit-3': {
        'en': 'CI/CD pipeline integration',
        'fr': 'Intégration de pipeline CI/CD',
        'es': 'Integración de pipeline CI/CD',
        'ro': 'Integrare pipeline CI/CD',
    },
    'github-benefit-4': {
        'en': 'Easy deployment to hosting platforms',
        'fr': 'Déploiement facile vers les plateformes d\'hébergement',
        'es': 'Fácil despliegue a plataformas de alojamiento',
        'ro': 'Implementare ușoară către platformele de găzduire',
    },
    'chapter-10-best-practices': {
        'en': '10. Best Practices',
        'fr': '10. Meilleures Pratiques',
        'es': '10. Mejores Prácticas',
        'ro': '10. Cele Mai Bune Practici',
    },
    'best-practices-title': {
        'en': 'Best Practices for Application Design',
        'fr': 'Meilleures Pratiques pour la Conception d\'Applications',
        'es': 'Mejores Prácticas para el Diseño de Aplicaciones',
        'ro': 'Cele Mai Bune Practici pentru Proiectarea Aplicațiilor',
    },
    'bp-1-title': {
        'en': 'Start Simple',
        'fr': 'Commencez Simple',
        'es': 'Comience Simple',
        'ro': 'Începeți Simplu',
    },
    'bp-1-desc': {
        'en': 'Begin with a minimal schema and iterate',
        'fr': 'Commencez avec un schéma minimal et itérez',
        'es': 'Comience con un esquema mínimo y itere',
        'ro': 'Începeți cu o schemă minimală și iterați',
    },
    'bp-2-title': {
        'en': 'Use Descriptive Names',
        'fr': 'Utilisez des Noms Descriptifs',
        'es': 'Use Nombres Descriptivos',
        'ro': 'Folosiți Nume Descriptive',
    },
    'bp-2-desc': {
        'en': 'Name entities and fields clearly (e.g., "customer" not "c")',
        'fr': 'Nommez clairement les entités et champs (par exemple, "client" pas "c")',
        'es': 'Nombre entidades y campos claramente (ej. "cliente" no "c")',
        'ro': 'Numiți clar entitățile și câmpurile (de ex. "client" nu "c")',
    },
    'bp-3-title': {
        'en': 'Write Good AI Instructions',
        'fr': 'Écrivez de Bonnes Instructions IA',
        'es': 'Escriba Buenas Instrucciones de IA',
        'ro': 'Scrieți Instrucțiuni IA Bune',
    },
    'bp-3-desc': {
        'en': 'Be specific about validation, business logic, and UI requirements',
        'fr': 'Soyez précis sur la validation, la logique métier et les exigences d\'interface',
        'es': 'Sea específico sobre validación, lógica de negocio y requisitos de UI',
        'ro': 'Fiți specific despre validare, logică de afaceri și cerințe de interfață',
    },
    'bp-4-title': {
        'en': 'Test in Sandbox',
        'fr': 'Testez dans le Bac à Sable',
        'es': 'Pruebe en Sandbox',
        'ro': 'Testați în Sandbox',
    },
    'bp-4-desc': {
        'en': 'Thoroughly test your schema before generating code',
        'fr': 'Testez soigneusement votre schéma avant de générer du code',
        'es': 'Pruebe exhaustivamente su esquema antes de generar código',
        'ro': 'Testați temeinic schema înainte de a genera cod',
    },
    'bp-5-title': {
        'en': 'Use Modules Wisely',
        'fr': 'Utilisez les Modules Sagement',
        'es': 'Use Módulos Sabiamente',
        'ro': 'Folosiți Modulele cu Înțelepciune',
    },
    'bp-5-desc': {
        'en': 'Only enable modules you actually need',
        'fr': 'Activez uniquement les modules dont vous avez réellement besoin',
        'es': 'Habilite solo los módulos que realmente necesita',
        'ro': 'Activați doar modulele de care aveți nevoie',
    },
    'bp-6-title': {
        'en': 'Version Control Early',
        'fr': 'Contrôle de Version Tôt',
        'es': 'Control de Versiones Temprano',
        'ro': 'Controlul Versiunilor Devreme',
    },
    'bp-6-desc': {
        'en': 'Push to GitHub as soon as you generate code',
        'fr': 'Poussez vers GitHub dès que vous générez du code',
        'es': 'Empuje a GitHub tan pronto como genere código',
        'ro': 'Împingeți către GitHub imediat ce generați cod',
    },
    'common-mistakes': {
        'en': 'Common Mistakes to Avoid',
        'fr': 'Erreurs Courantes à Éviter',
        'es': 'Errores Comunes a Evitar',
        'ro': 'Greșeli Comune de Evitat',
    },
    'mistake-1': {
        'en': 'Creating too many entities at once',
        'fr': 'Créer trop d\'entités à la fois',
        'es': 'Crear demasiadas entidades a la vez',
        'ro': 'Crearea prea multor entități deodată',
    },
    'mistake-2': {
        'en': 'Not testing relationships in sandbox',
        'fr': 'Ne pas tester les relations dans le bac à sable',
        'es': 'No probar relaciones en sandbox',
        'ro': 'Netestarea relațiilor în sandbox',
    },
    'mistake-3': {
        'en': 'Vague AI instructions',
        'fr': 'Instructions IA vagues',
        'es': 'Instrucciones de IA vagas',
        'ro': 'Instrucțiuni IA vagi',
    },
    'mistake-4': {
        'en': 'Generating code before testing',
        'fr': 'Générer du code avant de tester',
        'es': 'Generar código antes de probar',
        'ro': 'Generarea codului înainte de testare',
    },
    'need-help': {
        'en': 'Need Help?',
        'fr': 'Besoin d\'Aide ?',
        'es': '¿Necesita Ayuda?',
        'ro': 'Aveți Nevoie de Ajutor?',
    },
    'help-description': {
        'en': 'If you have questions or need assistance, our support team is here to help.',
        'fr': 'Si vous avez des questions ou besoin d\'assistance, notre équipe de support est là pour vous aider.',
        'es': 'Si tiene preguntas o necesita asistencia, nuestro equipo de soporte está aquí para ayudarle.',
        'ro': 'Dacă aveți întrebări sau aveți nevoie de asistență, echipa noastră de suport este aici pentru a vă ajuta.',
    },
    'contact-support': {
        'en': 'Contact Support',
        'fr': 'Contacter le Support',
        'es': 'Contactar Soporte',
        'ro': 'Contactați Suportul',
    },
    'applications': {
        'en': 'Applications',
        'fr': 'Applications',
        'es': 'Aplicaciones',
        'ro': 'Aplicații',
    },
    'cdate': {
        'en': 'Created',
        'fr': 'Créé le',
        'es': 'Creado',
        'ro': 'Creat la',
    },
    'confirm-delete-record': {
        'en': 'Confirm to delete this record.',
        'fr': 'Confirmez la suppression de cet enregistrement.',
        'es': 'Confirmar para eliminar este registro.',
        'ro': 'Confirmă ștergerea acestei înregistrări.',
    },
    'count-of': {
        'en': 'of',
        'fr': 'de',
        'es': 'de',
        'ro': 'de',
    },
    'count-to': {
        'en': 'to',
        'fr': 'à',
        'es': 'a',
        'ro': 'la',
    },
    'delete': {
        'en': 'Delete',
        'fr': 'Supprimer',
        'es': 'Eliminar',
        'ro': 'Șterge',
    },
    'description': {
        'en': 'Description',
        'fr': 'Description',
        'es': 'Descripción',
        'ro': 'Descriere',
    },
    'ai-instructions-app-help': {
        'en': 'Please give precises instructions for the AI to generate the entities, their fields and their relations. You will be able to control them one by one later.',
        'fr': 'Veuillez donner des instructions précises à l\'IA pour générer les entités, leurs champs et leurs relations. Vous pourrez les contrôler un par un plus tard.',
        'es': 'Por favor, dé instrucciones precisas a la IA para generar las entidades, sus campos y sus relaciones. Podrás controlarlos uno por uno más tarde.',
        'ro': 'Vă rugăm să daţi instrucţiuni precise IA-ului pentru a genera entităţile, câmpurile şi relaţiile lor. Veţi putea să le controlaţi unul câte unul mai târziu.',
    },
    'ai-instructions-help': {
        'en': 'Please give here the instructions to the AI',
        'fr': 'Veuillez donner ici les instructions à l\'IA',
        'es': 'Por favor, dé aquí las instrucciones a la IA',
        'ro': 'Vă rugăm să daţi aici instrucţiunile IA-ului',
    },
    'modules-needed': {
        'en': 'Additional features',
        'fr': 'Fonctionnalités supplémentaires',
        'es': 'Características adicionales',
        'ro': 'Funcționalități suplimentare',
    },
    'user-module': {
        'en': 'User management and authentication',
        'fr': 'Gestion des utilisateurs et authentification',
        'es': 'Gestión de usuarios y autenticación',
        'ro': 'Gestionare utilizatori și autentificare',
    },
    'subscription-module': {
        'en': 'Subscription management',
        'fr': 'Gestion des abonnements',
        'es': 'Gestión de suscripciones',
        'ro': 'Gestiunea abonamentelor',
    },
    'i18n-module': {
        'en': 'Multi-language',
        'fr': 'Multi-langues',
        'es': 'Multi-idioma',
        'ro': 'Multi-limbi',
    },
    'support-module': {
        'en': 'Ticket management system',
        'fr': 'Système de gestion des tickets',
        'es': 'Sistema de gestión de tickets',
        'ro': 'Sistem de gestionare a tichetelor',
    },
    'contact-module': {
        'en': 'Contact',
        'fr': 'Contact',
        'es': 'Contacto',
        'ro': 'Contact',
    },
    'cookie-module': {
        'en': 'Cookie consent management',
        'fr': 'Gestion du consentement des cookies',
        'es': 'Gestión del consentimiento de cookies',
        'ro': 'Gestionarea consimțământului pentru cookie-uri',
    },
    'none': {
        'en': 'None',
        'fr': 'Aucun',
        'es': 'Ninguno',
        'ro': 'Niciunul',
    },
    'additional-languages': {
        'en': 'Additional languages',
        'fr': 'Langues supplémentaires',
        'es': 'Idiomas adicionales',
        'ro': 'Limbi suplimentare',
    },
    'main-language': {
        'en': 'Main language',
        'fr': 'Langue principale',
        'es': 'Idioma principal',
        'ro': 'Limba principală',
    },
    'select-language': {
        'en': 'Select language',
        'fr': 'Sélectionner une langue',
        'es': 'Seleccionar idioma',
        'ro': 'Selectează limba',
    },
    'select-languages': {
        'en': 'Select languages',
        'fr': 'Sélectionner des langues',
        'es': 'Seleccionar idiomas',
        'ro': 'Selectează limbile',
    },
    'user-auto-selected-tooltip': {
        'en': 'User module is automatically selected because subscription or support modules require authentication',
        'fr': 'Le module Utilisateur est automatiquement sélectionné car les modules abonnement ou support nécessitent une authentification',
        'es': 'El módulo Usuario se selecciona automáticamente porque los módulos de suscripción o soporte requieren autenticación',
        'ro': 'Modulul Utilizator este selectat automat deoarece modulele de abonament sau suport necesită autentificare',
    },
    'auto-selected': {
        'en': 'auto-selected',
        'fr': 'selection automatique',
        'es': 'seleccion automatica',
        'ro': 'selectare automata',
    },
    'edit': {
        'en': 'Modify',
        'fr': 'Modifier',
        'es': 'Modificar',
        'ro': 'Modifică',
    },
    'entities': {
        'en': 'Entities',
        'fr': 'Entités',
        'es': 'Entidades',
        'ro': 'Entități',
    },
    'entitys': {
        'en': 'Entities',
        'fr': 'Entités',
        'es': 'Entidades',
        'ro': 'Entități',
    },
    'entity-self-relationship': {
        'en': 'An entity cannot have a relationship with itself.',
        'fr': 'Une entité ne peut pas avoir une relation avec elle-même.',
        'es': 'Una entidad no puede tener una relación consigo misma.',
        'ro': 'O entitate nu poate avea o relație cu ea însăși.',
    },
    'entity-wrong-application': {
        'en': 'This entity does not belong to the same application.',
        'fr': "Cette entité n'appartient pas à la même application.",
        'es': 'Esta entidad no pertenece a la misma aplicación.',
        'ro': 'Această entitate nu aparține aceleiași aplicații.',
    },
    'error-occured': {
        'en': 'Error in the form !',
        'fr': 'Erreur dans le formulaire !',
        'es': '¡Error en el formulario!',
        'ro': 'Eroare în formular!',
    },
    'fields': {
        'en': 'Fields',
        'fr': 'Champs',
        'es': 'Campos',
        'ro': 'Câmpuri',
    },
    'fields-mandatory': {
        'en': 'Mandatory fields',
        'fr': 'Champs obligatoires',
        'es': 'Campos obligatorios',
        'ro': 'Câmpuri obligatorii',
    },
    'field-type': {
        'en': 'Field type',
        'fr': 'Type de champ',
        'es': 'Tipo de campo',
        'ro': 'Tip câmp',
    },
    'field-type-boolean': {
        'en': 'Boolean',
        'fr': 'Booléen',
        'es': 'Booleano',
        'ro': 'Boolean',
    },
    'field-type-date': {
        'en': 'Date',
        'fr': 'Date',
        'es': 'Fecha',
        'ro': 'Dată',
    },
    'field-type-datetime': {
        'en': 'DateTime',
        'fr': 'Date et heure',
        'es': 'Fecha y hora',
        'ro': 'Dată și oră',
    },
    'field-type-decimal': {
        'en': 'Decimal',
        'fr': 'Décimal',
        'es': 'Decimal',
        'ro': 'Zecimal',
    },
    'field-type-file': {
        'en': 'File',
        'fr': 'Fichier',
        'es': 'Archivo',
        'ro': 'Fișier',
    },
    'field-type-fk': {
        'en': 'Foreign Key',
        'fr': 'Clé étrangère',
        'es': 'Clave foránea',
        'ro': 'Cheie externă',
    },
    'field-type-integer': {
        'en': 'Integer',
        'fr': 'Entier',
        'es': 'Entero',
        'ro': 'Întreg',
    },
    'field-type-m2m': {
        'en': 'Many to Many',
        'fr': 'Plusieurs à plusieurs',
        'es': 'Muchos a muchos',
        'ro': 'Mulți la mulți',
    },
    'field-type-string': {
        'en': 'String',
        'fr': 'Chaîne',
        'es': 'Cadena',
        'ro': 'Șir',
    },
    'field-type-text': {
        'en': 'Text',
        'fr': 'Texte',
        'es': 'Texto',
        'ro': 'Text',
    },
    'generator': {
        'en': 'Generator',
        'fr': 'Générateur',
        'es': 'Generador',
        'ro': 'Generator',
    },
    'generator-documentation': {
        'en': 'Application Generator Documentation',
        'fr': 'Documentation du Générateur d\'Applications',
        'es': 'Documentación del Generador de Aplicaciones',
        'ro': 'Documentația Generatorului de Aplicații',
    },
    'inactive': {
        'en': 'Inactive',
        'fr': 'Inactif',
        'es': 'Inactivo',
        'ro': 'Inactiv',
    },
    'language-en': {
        'en': 'English',
        'fr': 'Anglais',
        'es': 'Inglés',
        'ro': 'Engleză',
    },
    'language-es': {
        'en': 'Spanish',
        'fr': 'Espagnol',
        'es': 'Español',
        'ro': 'Spaniolă',
    },
    'language-fr': {
        'en': 'French',
        'fr': 'Français',
        'es': 'Francés',
        'ro': 'Franceză',
    },
    'language-ro': {
        'en': 'Romanian',
        'fr': 'Roumain',
        'es': 'Rumano',
        'ro': 'Română',
    },
    'languages': {
        'en': 'Languages',
        'fr': 'Langues',
        'es': 'Idiomas',
        'ro': 'Limbi',
    },
    'languages-placeholder': {
        'en': 'Select languages…',
        'fr': 'Sélectionnez des langues…',
        'es': 'Selecciona idiomas…',
        'ro': 'Selectați limbi…',
    },
    'name': {
        'en': 'Name',
        'fr': 'Nom',
        'es': 'Nombre',
        'ro': 'Nume',
    },
    'no-application-yet-add-first': {
        'en': 'No application yet — add your first one',
        'fr': 'Aucune application — ajoutez-en une',
        'es': 'Sin aplicaciones — añade la primera',
        'ro': 'Nicio aplicație — adaugă prima',
    },
    'no-entity-yet-add-first': {
        'en': 'No entity yet — add your first one',
        'fr': 'Aucune entité — ajoutez-en une',
        'es': 'Sin entidades — añade la primera',
        'ro': 'Nicio entitate — adaugă prima',
    },
    'no-field-yet-add-first': {
        'en': 'No field yet — add your first one',
        'fr': 'Aucun champ — ajoutez-en un',
        'es': 'Sin campos — añade el primero',
        'ro': 'Niciun câmp — adaugă primul',
    },
    'not-exists': {
        'en': 'Record not found.',
        'fr': 'Enregistrement introuvable.',
        'es': 'Registro no encontrado.',
        'ro': 'Înregistrarea nu există.',
    },
    'not-required': {
        'en': 'Not required',
        'fr': 'Facultatif',
        'es': 'Opcional',
        'ro': 'Opțional',
    },
    'relation-many-to-many': {
        'en': 'Many to Many',
        'fr': 'Plusieurs à plusieurs',
        'es': 'Muchos a muchos',
        'ro': 'Mulți la mulți',
    },
    'relation-one-to-many': {
        'en': 'One to Many',
        'fr': 'Un à plusieurs',
        'es': 'Uno a muchos',
        'ro': 'Unu la mulți',
    },
    'relation-one-to-one': {
        'en': 'One to One',
        'fr': 'Un à un',
        'es': 'Uno a uno',
        'ro': 'Unu la unu',
    },
    'relationship': {
        'en': 'Relationship',
        'fr': 'Relation',
        'es': 'Relación',
        'ro': 'Relație',
    },
    'relationships': {
        'en': 'Relationships',
        'fr': 'Relations',
        'es': 'Relaciones',
        'ro': 'Relații',
    },
    'relation-type': {
        'en': 'Relation type',
        'fr': 'Type de relation',
        'es': 'Tipo de relación',
        'ro': 'Tip relație',
    },
    'remove-relationship': {
        'en': 'Remove relationship',
        'fr': 'Supprimer la relation',
        'es': 'Eliminar relación',
        'ro': 'Elimină relația',
    },
    'required': {
        'en': 'Required',
        'fr': 'Obligatoire',
        'es': 'Obligatorio',
        'ro': 'Obligatoriu',
    },
    'role': {
        'en': 'Role',
        'fr': 'Rôle',
        'es': 'Rol',
        'ro': 'Rol',
    },
    'role-controller': {
        'en': 'Controller',
        'fr': 'Contrôleur',
        'es': 'Controlador',
        'ro': 'Controler',
    },
    'role-model': {
        'en': 'Model',
        'fr': 'Modèle',
        'es': 'Modelo',
        'ro': 'Model',
    },
    'role-service': {
        'en': 'Service',
        'fr': 'Service',
        'es': 'Servicio',
        'ro': 'Serviciu',
    },
    'role-utility': {
        'en': 'Utility',
        'fr': 'Utilitaire',
        'es': 'Utilidad',
        'ro': 'Utilitar',
    },
    'select-application': {
        'en': 'Application',
        'fr': 'Application',
        'es': 'Aplicación',
        'ro': 'Aplicație',
    },
    'select-application-placeholder': {
        'en': 'Select an application…',
        'fr': 'Sélectionnez une application…',
        'es': 'Selecciona una aplicación…',
        'ro': 'Selectați o aplicație…',
    },
    'select-application-to-see-entities': {
        'en': 'Please select an application to view its entities.',
        'fr': 'Veuillez sélectionner une application pour voir ses entités.',
        'es': 'Selecciona una aplicación para ver sus entidades.',
        'ro': 'Selectați o aplicație pentru a vedea entitățile sale.',
    },
    'select-application-to-see-fields': {
        'en': 'Please select an application to get started.',
        'fr': 'Veuillez sélectionner une application pour commencer.',
        'es': 'Selecciona una aplicación para comenzar.',
        'ro': 'Selectați o aplicație pentru a începe.',
    },
    'select-entity': {
        'en': 'Entity',
        'fr': 'Entité',
        'es': 'Entidad',
        'ro': 'Entitate',
    },
    'select-entity-placeholder': {
        'en': 'Select an entity…',
        'fr': 'Sélectionnez une entité…',
        'es': 'Selecciona una entidad…',
        'ro': 'Selectați o entitate…',
    },
    'select-entity-to-see-fields': {
        'en': 'Please select an entity to view its fields.',
        'fr': 'Veuillez sélectionner une entité pour voir ses champs.',
        'es': 'Selecciona una entidad para ver sus campos.',
        'ro': 'Selectați o entitate pentru a vedea câmpurile sale.',
    },
    'show-less': {
        'en': 'Show less',
        'fr': 'Voir moins',
        'es': 'Ver menos',
        'ro': 'Vezi mai puțin',
    },
    'show-more': {
        'en': 'Show more',
        'fr': 'Voir plus',
        'es': 'Ver más',
        'ro': 'Vezi mai mult',
    },
    'status': {
        'en': 'Status',
        'fr': 'Statut',
        'es': 'Estado',
        'ro': 'Stare',
    },
    'status-draft': {
        'en': 'Draft',
        'fr': 'Brouillon',
        'es': 'Borrador',
        'ro': 'Ciornă',
    },
    'status-generated': {
        'en': 'Generated',
        'fr': 'Généré',
        'es': 'Generado',
        'ro': 'Generat',
    },
    'status-ongoing': {
        'en': 'Ongoing',
        'fr': 'En cours',
        'es': 'En progreso',
        'ro': 'În curs',
    },
    'successfully-deleted': {
        'en': '{{entity}} successfully deleted.',
        'fr': '{{entity}} supprimé avec succès.',
        'es': '{{entity}} eliminado correctamente.',
        'ro': '{{entity}} șters cu succes.',
    },
    'successfully-saved': {
        'en': '{{entity}} successfully saved.',
        'fr': '{{entity}} enregistré avec succès.',
        'es': '{{entity}} guardado correctamente.',
        'ro': '{{entity}} salvat cu succes.',
    },
    'successfully-updated': {
        'en': '{{entity}} successfully updated.',
        'fr': '{{entity}} mis à jour avec succès.',
        'es': '{{entity}} actualizado correctamente.',
        'ro': '{{entity}} actualizat cu succes.',
    },
    'tech-stack': {
        'en': 'Tech stack',
        'fr': 'Stack technique',
        'es': 'Stack tecnológico',
        'ro': 'Stack tehnologic',
    },
    'to-entity': {
        'en': 'Target entity',
        'fr': 'Entité cible',
        'es': 'Entidad destino',
        'ro': 'Entitate țintă',
    },
    'update-application': {
        'en': 'Update application',
        'fr': "Modifier l'application",
        'es': 'Actualizar aplicación',
        'ro': 'Actualizează aplicația',
    },
    'update-entity': {
        'en': 'Update entity',
        'fr': "Modifier l'entité",
        'es': 'Actualizar entidad',
        'ro': 'Actualizează entitatea',
    },
    'update-field': {
        'en': 'Update field',
        'fr': 'Modifier le champ',
        'es': 'Actualizar campo',
        'ro': 'Actualizează câmpul',
    },
    'validate': {
        'en': 'Validate',
        'fr': 'Valider',
        'es': 'Validar',
        'ro': 'Validează',
    },
    'view-entities': {
        'en': 'View entities',
        'fr': 'Voir les entités',
        'es': 'Ver entidades',
        'ro': 'Vezi entitățile',
    },
    'view-fields': {
        'en': 'View fields',
        'fr': 'Voir les champs',
        'es': 'Ver campos',
        'ro': 'Vezi câmpurile',
    },
    'sandbox': {
        'en': 'Sandbox',
        'fr': 'Bac à sable',
        'es': 'Sandbox',
        'ro': 'Sandbox',
    },
    'refresh-config': {
        'en': 'Refresh Config',
        'fr': 'Actualiser la config',
        'es': 'Actualizar config',
        'ro': 'Reîncărca config',
    },
    'loading': {
        'en': 'Loading...',
        'fr': 'Chargement...',
        'es': 'Cargando...',
        'ro': 'Se încarcă...',
    },
    'ai-loading': {
        'en': 'Please wait while AI is processing...',
        'fr': "Veuillez patienter pendant que l'IA traite...",
        'es': 'Por favor espere mientras la IA procesa...',
        'ro': 'Vă rugăm să așteptați în timp ce AI-ul procesează...',
    },
    'ai-error': {
        'en': 'AI interpretation failed. Using default configuration.',
        'fr': "L'interprétation IA a échoué. Utilisation de la configuration par défaut.",
        'es': 'La interpretación de IA falló. Usando configuración predeterminada.',
        'ro': 'Interpretarea IA a eșuat. Se folosește configurația implicită.',
    },
    'refreshed': {
        'en': 'Sandbox config refreshed',
        'fr': 'Config du sandbox actualisée',
        'es': 'Config del sandbox actualizada',
        'ro': 'Config sandbox reîncărcată',
    },
    'refresh-config-with-ai': {
        'en': 'Refresh Config with AI',
        'fr': 'Actualiser la config avec IA',
        'es': 'Actualizar config con IA',
        'ro': 'Reîncărcați config cu IA',
    },
    'refresh-config-full': {
        'en': 'Full AI Refresh',
        'fr': 'Actualisation IA complète',
        'es': 'Actualización IA completa',
        'ro': 'Reîmprospătare IA completă',
    },
    'refresh-config-full-warning': {
        'en': 'This will replace ALL entity display configurations with a fresh AI-generated version. Any manual customisations will be lost.',
        'fr': 'Cela remplacera TOUTES les configurations d\'affichage des entités par une version générée par l\'IA. Toutes les personnalisations manuelles seront perdues.',
        'es': 'Esto reemplazará TODAS las configuraciones de visualización de entidades con una versión generada por IA. Se perderán todas las personalizaciones manuales.',
        'ro': 'Aceasta va înlocui TOATE configurațiile de afișare a entităților cu o versiune generată de IA. Orice personalizări manuale vor fi pierdute.',
    },
    'ai-confirm-refresh': {
        'en': 'Regenerate the full sandbox configuration with AI? This replaces ALL entity display settings.',
        'fr': 'Régénérer la configuration complète du sandbox avec l\'IA ? Cela remplace TOUS les paramètres d\'affichage des entités.',
        'es': '¿Regenerar la configuración completa del sandbox con IA? Esto reemplaza TODOS los ajustes de visualización de entidades.',
        'ro': 'Regenerați configurația completă a sandbox-ului cu IA? Aceasta înlocuiește TOATE setările de afișare ale entităților.',
    },
    'refresh-config-partial': {
        'en': 'Refresh with AI',
        'fr': 'Actualiser avec IA',
        'es': 'Actualizar con IA',
        'ro': 'Reîmprospătare cu IA',
    },
    'ai-confirm-refresh-partial': {
        'en': 'Regenerate the display configuration for "{{name}}" with AI? Only this entity\'s settings will be updated.',
        'fr': 'Régénérer la configuration d\'affichage pour "{{name}}" avec l\'IA ? Seuls les paramètres de cette entité seront mis à jour.',
        'es': '¿Regenerar la configuración de visualización para "{{name}}" con IA? Solo se actualizarán los ajustes de esta entidad.',
        'ro': 'Regenerați configurația de afișare pentru "{{name}}" cu IA? Vor fi actualizate doar setările acestei entități.',
    },
    'refreshed-partial': {
        'en': 'Config refreshed for {{name}}',
        'fr': 'Config actualisée pour {{name}}',
        'es': 'Config actualizada para {{name}}',
        'ro': 'Config reîncărcată pentru {{name}}',
    },
    'generate-seed-data': {
        'en': 'Generate Sample Data',
        'fr': 'Générer des données exemples',
        'es': 'Generar datos de ejemplo',
        'ro': 'Generați date exemplu',
    },
    'ai-confirm-seed': {
        'en': 'Generate AI sample data for {{name}}? This will create 10 records per entity.',
        'fr': 'Générer des données IA pour {{name}} ? Cela créera 10 enregistrements par entité.',
        'es': '¿Generar datos IA para {{name}}? Esto creará 10 registros por entidad.',
        'ro': 'Generați date IA pentru {{name}}? Aceasta va crea 10 înregistrări per entitate.',
    },
    'seed-data-generated': {
        'en': '{{count}} records generated',
        'fr': '{{count}} enregistrements générés',
        'es': '{{count}} registros generados',
        'ro': '{{count}} înregistrări generate',
    },
    'clear-all-data': {
        'en': 'Clear All Data',
        'fr': 'Effacer toutes les données',
        'es': 'Borrar todos los datos',
        'ro': 'Ștergeți toate datele',
    },
    'clear-all-data-confirm': {
        'en': 'Delete all sample data for "{{name}}"?',
        'fr': 'Supprimer toutes les données exemples de "{{name}}" ?',
        'es': '¿Eliminar todos los datos de ejemplo de "{{name}}"?',
        'ro': 'Ștergeți toate datele pentru "{{name}}"?',
    },
    'clear-all-data-warning': {
        'en': 'This action is irreversible. All records across every entity will be permanently deleted.',
        'fr': 'Cette action est irréversible. Tous les enregistrements de chaque entité seront définitivement supprimés.',
        'es': 'Esta acción es irreversible. Todos los registros de cada entidad serán eliminados permanentemente.',
        'ro': 'Această acțiune este ireversibilă. Toate înregistrările din fiecare entitate vor fi șterse permanent.',
    },
    'data-cleared': {
        'en': '{{count}} records deleted',
        'fr': '{{count}} enregistrements supprimés',
        'es': '{{count}} registros eliminados',
        'ro': '{{count}} înregistrări șterse',
    },
    'generate-seed-data-entity': {
        'en': 'Generate Data',
        'fr': 'Générer des données',
        'es': 'Generar datos',
        'ro': 'Generați date',
    },
    'ai-confirm-seed-entity': {
        'en': 'Generate 5 AI sample records for "{{name}}"? Existing records for this entity are kept.',
        'fr': 'Générer 5 enregistrements IA pour "{{name}}" ? Les enregistrements existants de cette entité sont conservés.',
        'es': '¿Generar 5 registros IA para "{{name}}"? Los registros existentes de esta entidad se conservan.',
        'ro': 'Generați 5 înregistrări IA pentru "{{name}}"? Înregistrările existente ale acestei entități sunt păstrate.',
    },
    'seed-data-generated-entity': {
        'en': '{{count}} records generated for {{name}}',
        'fr': '{{count}} enregistrements générés pour {{name}}',
        'es': '{{count}} registros generados para {{name}}',
        'ro': '{{count}} înregistrări generate pentru {{name}}',
    },
    'clear-entity-data': {
        'en': 'Clear Data',
        'fr': 'Effacer les données',
        'es': 'Borrar datos',
        'ro': 'Ștergeți datele',
    },
    'clear-entity-data-confirm': {
        'en': 'Delete all sample data for "{{name}}"? Only this entity\'s records will be removed.',
        'fr': 'Supprimer toutes les données exemples de "{{name}}" ? Seuls les enregistrements de cette entité seront supprimés.',
        'es': '¿Eliminar todos los datos de ejemplo de "{{name}}"? Solo se eliminarán los registros de esta entidad.',
        'ro': 'Ștergeți toate datele pentru "{{name}}"? Vor fi eliminate doar înregistrările acestei entități.',
    },
    'entity-data-cleared': {
        'en': '{{count}} records deleted for {{name}}',
        'fr': '{{count}} enregistrements supprimés pour {{name}}',
        'es': '{{count}} registros eliminados para {{name}}',
        'ro': '{{count}} înregistrări șterse pentru {{name}}',
    },
    'sandbox-needs-refresh': {
        'en': 'Sandbox Refresh',
        'fr': 'Actualisation Sandbox',
        'es': 'Actualización Sandbox',
        'ro': 'Actualizare Sandbox',
    },
    'sandbox-needs-refresh-message': {
        'en': 'The sandbox needs to be refreshed to include the latest changes made to the application. Please choose the refresh method.',
        'fr': 'Le bac à sable doit être actualisé pour inclure les derniers changements apportés à la application. Veuillez choisir la méthode de actualisation.',
        'es': 'El sandbox necesita actualizarse para incluir los últimos cambios realizados en la aplicación. Por favor elija el método de actualización.',
        'ro': 'Sandbox-ul trebuie reîmprospătat pentru a include ultimele modificări aduse aplicației. Vă rugăm să alegeți metoda de reîmprospătare.',
    },
    'use-ai': {
        'en': 'AI method',
        'fr': "Méthode IA",
        'es': 'Método IA',
        'ro': 'Metodă IA',
    },
    'no-thanks': {
        'en': 'Default method',
        'fr': 'Méthode par défaut',
        'es': 'Método predeterminado',
        'ro': 'Metodă implicită',
    },
    'upload-logo': {
        'en': 'Upload Logo',
        'fr': 'Téléverser logo',
        'es': 'Subir logo',
        'ro': 'Încarcă logo',
    },
    'uploading': {
        'en': 'Uploading...',
        'fr': 'Téléversement...',
        'es': 'Subiendo...',
        'ro': 'Se încarcă...',
    },
    'logo-uploaded': {
        'en': 'Logo uploaded successfully',
        'fr': 'Logo téléchargé avec succès',
        'es': 'Logo subido con éxito',
        'ro': 'Logo încărcat cu succes',
    },
    'only-svg-allowed': {
        'en': 'Only SVG files are allowed',
        'fr': 'Seuls les fichiers SVG sont autorisés',
        'es': 'Solo se permiten archivos SVG',
        'ro': 'Sunt permise doar fișiere SVG',
    },
    'sandbox-config-issues': {
        'en': 'Sandbox config issues',
        'fr': 'Problèmes de config sandbox',
        'es': 'Problemas de config sandbox',
        'ro': 'Probleme config sandbox',
    },
    'errors': {
        'en': 'errors',
        'fr': 'erreurs',
        'es': 'errores',
        'ro': 'erori',
    },
    'warnings': {
        'en': 'warnings',
        'fr': 'avertissements',
        'es': 'advertencias',
        'ro': 'avertismente',
    },

    # --- Workflow ---
    'ai-refresh-workflow': {
        'en': 'Refresh Workflow',
        'fr': 'Actualiser le Workflow',
        'es': 'Actualizar Flujo de Trabajo',
        'ro': 'Reîmprospătează Fluxul de Lucru',
    },
    'move-up': {
        'en': 'Move up',
        'fr': 'Déplacer vers le haut',
        'es': 'Mover arriba',
        'ro': 'Mută în sus',
    },
    'move-down': {
        'en': 'Move down',
        'fr': 'Déplacer vers le bas',
        'es': 'Mover abajo',
        'ro': 'Mută în jos',
    },
    'ai-confirm-refresh-partial': {
        'en': 'Refresh this entity configuration with AI?',
        'fr': 'Actualiser la configuration de cette entité avec l\'IA ?',
        'es': '¿Actualizar la configuración de esta entidad con IA?',
        'ro': 'Reîmprospătați configurația acestei entități cu IA?',
    },
    'refresh-config-partial': {
        'en': 'Refresh Entity Config',
        'fr': 'Actualiser la Config de l\'Entité',
        'es': 'Actualizar Config de Entidad',
        'ro': 'Reîmprospătează Config Entitate',
    },
    'ai-confirm-refresh-full': {
        'en': 'Refresh all entities configuration with AI?',
        'fr': 'Actualiser la configuration de toutes les entités avec l\'IA ?',
        'es': '¿Actualizar la configuración de todas las entidades con IA?',
        'ro': 'Reîmprospătați configurația tuturor entităților cu IA?',
    },
    'refresh-config-full': {
        'en': 'Refresh All Config',
        'fr': 'Actualiser Toute la Config',
        'es': 'Actualizar Toda la Config',
        'ro': 'Reîmprospătează Toată Config',
    },
    'refresh-config-full-warning': {
        'en': 'This will regenerate configurations for all entities. Existing sandbox data will be preserved.',
        'fr': 'Cela régénérera les configurations pour toutes les entités. Les données sandbox existantes seront conservées.',
        'es': 'Esto regenerará las configuraciones para todas las entidades. Los datos sandbox existentes se conservarán.',
        'ro': 'Acest lucru va regenera configurațiile pentru toate entitățile. Datele sandbox existente vor fi păstrate.',
    },
    'session-expired': {
        'en': 'Session Expired',
        'fr': 'Session Expirée',
        'es': 'Sesión Expirada',
        'ro': 'Sesiune Expirată',
    },
    'workflow': {
        'en': 'Workflow',
        'fr': 'Workflow',
        'es': 'Flujo de trabajo',
        'ro': 'Flux de lucru',
    },
    'workflow-description': {
        'en': 'Workflow description',
        'fr': 'Description du workflow',
        'es': 'Descripción del flujo',
        'ro': 'Descrierea fluxului',
    },
    'workflow-description-help': {
        'en': 'Describe the overall flow of your application: how users navigate between entities, what happens step by step. This helps the AI choose the right display mode and plugins.',
        'fr': "Décrivez le flux global de votre application : comment les utilisateurs naviguent entre les entités, ce qui se passe étape par étape. Cela aide l'IA à choisir le bon mode d'affichage et les bons plugins.",
        'es': 'Describe el flujo general de tu aplicación: cómo los usuarios navegan entre entidades, qué ocurre paso a paso. Esto ayuda a la IA a elegir el modo de visualización y los plugins correctos.',
        'ro': 'Descrieți fluxul general al aplicației: cum navighează utilizatorii între entități, ce se întâmplă pas cu pas. Aceasta ajută AI-ul să aleagă modul de afișare și pluginurile potrivite.',
    },
    'workflow-steps': {
        'en': 'Workflow steps',
        'fr': 'Étapes du workflow',
        'es': 'Pasos del flujo',
        'ro': 'Pașii fluxului',
    },
    'add-workflow-step': {
        'en': 'Add step',
        'fr': 'Ajouter une étape',
        'es': 'Agregar paso',
        'ro': 'Adaugă pas',
    },
    'no-workflow-steps': {
        'en': 'No steps yet — add the first one to describe your workflow.',
        'fr': "Aucune étape — ajoutez la première pour décrire votre workflow.",
        'es': 'Sin pasos aún — añada el primero para describir su flujo.',
        'ro': 'Niciun pas — adaugați primul pentru a descrie fluxul.',
    },
    'workflow-step-entity': {
        'en': 'Entity',
        'fr': 'Entité',
        'es': 'Entidad',
        'ro': 'Entitate',
    },
    'workflow-step-action': {
        'en': 'Action',
        'fr': 'Action',
        'es': 'Acción',
        'ro': 'Acțiune',
    },
    'workflow-step-trigger': {
        'en': 'Trigger / context',
        'fr': 'Déclencheur / contexte',
        'es': 'Disparador / contexto',
        'ro': 'Declanșator / context',
    },
    'workflow-step-trigger-help': {
        'en': 'What triggers this step? (e.g. "user clicks Add plant", "after placing a zone on the canvas")',
        'fr': 'Qu\'est-ce qui déclenche cette étape ? (ex : "l\'utilisateur clique sur Ajouter une plante", "après avoir placé une zone sur le canevas")',
        'es': '¿Qué desencadena este paso? (ej.: "el usuario hace clic en Agregar planta", "después de colocar una zona en el lienzo")',
        'ro': 'Ce declanșează acest pas? (ex.: "utilizatorul face clic pe Adăugare plantă", "după plasarea unei zone pe canvas")',
    },
    'workflow-step-ai-instructions': {
        'en': 'AI instructions for this step',
        'fr': 'Instructions IA pour cette étape',
        'es': 'Instrucciones IA para este paso',
        'ro': 'Instrucțiuni IA pentru acest pas',
    },
    'workflow-step-order': {
        'en': 'Order',
        'fr': 'Ordre',
        'es': 'Orden',
        'ro': 'Ordine',
    },
    'action-create': {
        'en': 'Create',
        'fr': 'Créer',
        'es': 'Crear',
        'ro': 'Creare',
    },
    'action-list': {
        'en': 'List / Browse',
        'fr': 'Lister / Parcourir',
        'es': 'Listar / Explorar',
        'ro': 'Listare / Navigare',
    },
    'action-view': {
        'en': 'View details',
        'fr': 'Voir les détails',
        'es': 'Ver detalles',
        'ro': 'Vizualizare detalii',
    },
    'action-update': {
        'en': 'Update',
        'fr': 'Mettre à jour',
        'es': 'Actualizar',
        'ro': 'Actualizare',
    },
    'action-delete': {
        'en': 'Delete',
        'fr': 'Supprimer',
        'es': 'Eliminar',
        'ro': 'Ștergere',
    },
    'action-assign': {
        'en': 'Assign / Link',
        'fr': 'Assigner / Lier',
        'es': 'Asignar / Vincular',
        'ro': 'Atribuire / Legare',
    },
    'action-compute': {
        'en': 'Compute / Calculate',
        'fr': 'Calculer',
        'es': 'Calcular',
        'ro': 'Calculare',
    },
    'action-draw': {
        'en': 'Draw / Place on canvas',
        'fr': 'Dessiner / Placer sur le canevas',
        'es': 'Dibujar / Colocar en lienzo',
        'ro': 'Desenare / Plasare pe canvas',
    },
    'action-plan': {
        'en': 'Plan / Schedule',
        'fr': 'Planifier',
        'es': 'Planificar',
        'ro': 'Planificare',
    },
    'action-record': {
        'en': 'Record / Log',
        'fr': 'Enregistrer / Journaliser',
        'es': 'Registrar / Registrar',
        'ro': 'Înregistrare / Jurnal',
    },
    'action-search': {
        'en': 'Search / Filter',
        'fr': 'Rechercher / Filtrer',
        'es': 'Buscar / Filtrar',
        'ro': 'Căutare / Filtrare',
    },
    'action-export': {
        'en': 'Export',
        'fr': 'Exporter',
        'es': 'Exportar',
        'ro': 'Export',
    },
    'workflow-saved': {
        'en': 'Workflow saved',
        'fr': 'Workflow enregistré',
        'es': 'Flujo guardado',
        'ro': 'Flux salvat',
    },
    'workflow-ai-refreshed': {
        'en': 'AI workflow generated successfully',
        'fr': 'Workflow IA généré avec succès',
        'es': 'Flujo de trabajo IA generado con éxito',
        'ro': 'Flux de lucru IA generat cu succes',
    },
    'ai-refresh-workflow': {
        'en': 'Generate with AI',
        'fr': 'Générer avec l\'IA',
        'es': 'Generar con IA',
        'ro': 'Generează cu IA',
    },
    'ai-refresh-workflow-confirm': {
        'en': 'This will replace the current workflow description and steps with an AI-generated proposition. Continue?',
        'fr': 'Cela remplacera la description et les étapes du workflow par une proposition générée par l\'IA. Continuer ?',
        'es': '¿Esto reemplazará la descripción y los pasos del flujo con una propuesta generada por IA. ¿Continuar?',
        'ro': 'Aceasta va înlocui descrierea și pașii fluxului cu o propunere generată de IA. Continuați?',
    },
}


# ===========================================================================
# entity
# (shared keys are linked via NAMESPACE_LINKS, not duplicated here)
# ===========================================================================
TRANSLATIONS['entity'] = {
    # --- Entities component expects t(`${entity}s`) for the page title ---
    'entitys': {
        'en': 'Entities',
        'fr': 'Entités',
        'es': 'Entidades',
        'ro': 'Entități',
    },
    # --- CRUD modal titles / empty state ---
    'add-entity': {
        'en': 'Add entity',
        'fr': 'Ajouter une entité',
        'es': 'Agregar entidad',
        'ro': 'Adaugă entitate',
    },
    'update-entity': {
        'en': 'Update entity',
        'fr': "Modifier l'entité",
        'es': 'Actualizar entidad',
        'ro': 'Actualizează entitatea',
    },
    'no-entity-yet-add-first': {
        'en': 'No entity yet — add your first one',
        'fr': 'Aucune entité — ajoutez-en une',
        'es': 'Sin entidades — añade la primera',
        'ro': 'Nicio entitate — adaugă prima',
    },
    # --- Role ---
    'role': {
        'en': 'Role',
        'fr': 'Rôle',
        'es': 'Rol',
        'ro': 'Rol',
    },
    'role-model': {
        'en': 'Model',
        'fr': 'Modèle',
        'es': 'Modelo',
        'ro': 'Model',
    },
    'role-service': {
        'en': 'Service',
        'fr': 'Service',
        'es': 'Servicio',
        'ro': 'Serviciu',
    },
    'role-controller': {
        'en': 'Controller',
        'fr': 'Contrôleur',
        'es': 'Controlador',
        'ro': 'Controler',
    },
    'role-utility': {
        'en': 'Utility',
        'fr': 'Utilitaire',
        'es': 'Utilidad',
        'ro': 'Utilitar',
    },
    # --- Relationships ---
    'relationships': {
        'en': 'Relationships',
        'fr': 'Relations',
        'es': 'Relaciones',
        'ro': 'Relații',
    },
    'relationship': {
        'en': 'Relationship',
        'fr': 'Relation',
        'es': 'Relación',
        'ro': 'Relație',
    },
    'add-relationship': {
        'en': 'Add relationship',
        'fr': 'Ajouter une relation',
        'es': 'Agregar relación',
        'ro': 'Adaugă relație',
    },
    'remove-relationship': {
        'en': 'Remove relationship',
        'fr': 'Supprimer la relation',
        'es': 'Eliminar relación',
        'ro': 'Elimină relația',
    },
    'to-entity': {
        'en': 'Target entity',
        'fr': 'Entité cible',
        'es': 'Entidad destino',
        'ro': 'Entitate țintă',
    },
    'relation-type': {
        'en': 'Relation type',
        'fr': 'Type de relation',
        'es': 'Tipo de relación',
        'ro': 'Tip relație',
    },
    'relation-one-to-one': {
        'en': 'One to One',
        'fr': 'Un à un',
        'es': 'Uno a uno',
        'ro': 'Unu la unu',
    },
    'relation-one-to-many': {
        'en': 'One to Many',
        'fr': 'Un à plusieurs',
        'es': 'Uno a muchos',
        'ro': 'Unu la mulți',
    },
    'relation-many-to-many': {
        'en': 'Many to Many',
        'fr': 'Plusieurs à plusieurs',
        'es': 'Muchos a muchos',
        'ro': 'Mulți la mulți',
    },
    # --- Navigation ---
    'view-fields': {
        'en': 'View fields',
        'fr': 'Voir les champs',
        'es': 'Ver campos',
        'ro': 'Vezi câmpurile',
    },
    'select-application': {
        'en': 'Application',
        'fr': 'Application',
        'es': 'Aplicación',
        'ro': 'Aplicație',
    },
    'select-application-placeholder': {
        'en': 'Select an application…',
        'fr': 'Sélectionnez une application…',
        'es': 'Selecciona una aplicación…',
        'ro': 'Selectați o aplicație…',
    },
    'select-application-to-see-entities': {
        'en': 'Please select an application to view its entities.',
        'fr': 'Veuillez sélectionner une application pour voir ses entités.',
        'es': 'Selecciona una aplicación para ver sus entidades.',
        'ro': 'Selectați o aplicație pentru a vedea entitățile sale.',
    },
    'select-entity': {
        'en': 'Entity',
        'fr': 'Entité',
        'es': 'Entidad',
        'ro': 'Entitate',
    },
    'select-entity-placeholder': {
        'en': 'Select an entity…',
        'fr': 'Sélectionnez une entité…',
        'es': 'Selecciona una entidad…',
        'ro': 'Selectați o entitate…',
    },
    # --- Errors ---
    'not-exists': {
        'en': 'Record not found.',
        'fr': 'Enregistrement introuvable.',
        'es': 'Registro no encontrado.',
        'ro': 'Înregistrarea nu există.',
    },
    'entity-wrong-application': {
        'en': 'This entity does not belong to the same application.',
        'fr': "Cette entité n'appartient pas à la même application.",
        'es': 'Esta entidad no pertenece a la misma aplicación.',
        'ro': 'Această entitate nu aparține aceleiași aplicații.',
    },
    'entity-self-relationship': {
        'en': 'An entity cannot have a relationship with itself.',
        'fr': 'Une entité ne peut pas avoir une relation avec elle-même.',
        'es': 'Una entidad no puede tener una relación consigo misma.',
        'ro': 'O entitate nu poate avea o relație cu ea însăși.',
    },
}


# ===========================================================================
# field
# (shared keys are linked via NAMESPACE_LINKS, not duplicated here)
# ===========================================================================
TRANSLATIONS['field'] = {
    # --- Entities component expects t(`${entity}s`) for the page title ---
    'fields': {
        'en': 'Fields',
        'fr': 'Champs',
        'es': 'Campos',
        'ro': 'Câmpuri',
    },
    # --- CRUD modal titles / empty state ---
    'add-field': {
        'en': 'Add field',
        'fr': 'Ajouter un champ',
        'es': 'Agregar campo',
        'ro': 'Adaugă câmp',
    },
    'update-field': {
        'en': 'Update field',
        'fr': 'Modifier le champ',
        'es': 'Actualizar campo',
        'ro': 'Actualizează câmpul',
    },
    'no-field-yet-add-first': {
        'en': 'No field yet — add your first one',
        'fr': 'Aucun champ — ajoutez-en un',
        'es': 'Sin campos — añade el primero',
        'ro': 'Niciun câmp — adaugă primul',
    },
    # --- Field types ---
    'field-type': {
        'en': 'Field type',
        'fr': 'Type de champ',
        'es': 'Tipo de campo',
        'ro': 'Tip câmp',
    },
    'field-type-string': {
        'en': 'String',
        'fr': 'Chaîne',
        'es': 'Cadena',
        'ro': 'Șir',
    },
    'field-type-text': {
        'en': 'Text',
        'fr': 'Texte',
        'es': 'Texto',
        'ro': 'Text',
    },
    'field-type-integer': {
        'en': 'Integer',
        'fr': 'Entier',
        'es': 'Entero',
        'ro': 'Întreg',
    },
    'field-type-decimal': {
        'en': 'Decimal',
        'fr': 'Décimal',
        'es': 'Decimal',
        'ro': 'Zecimal',
    },
    'field-type-boolean': {
        'en': 'Boolean',
        'fr': 'Booléen',
        'es': 'Booleano',
        'ro': 'Boolean',
    },
    'field-type-date': {
        'en': 'Date',
        'fr': 'Date',
        'es': 'Fecha',
        'ro': 'Dată',
    },
    'field-type-datetime': {
        'en': 'DateTime',
        'fr': 'Date et heure',
        'es': 'Fecha y hora',
        'ro': 'Dată și oră',
    },
    'field-type-file': {
        'en': 'File',
        'fr': 'Fichier',
        'es': 'Archivo',
        'ro': 'Fișier',
    },
    'field-type-fk': {
        'en': 'Foreign Key',
        'fr': 'Clé étrangère',
        'es': 'Clave foránea',
        'ro': 'Cheie externă',
    },
    'field-type-m2m': {
        'en': 'Many to Many',
        'fr': 'Plusieurs à plusieurs',
        'es': 'Muchos a muchos',
        'ro': 'Mulți la mulți',
    },
    # --- Navigation ---
    'select-application': {
        'en': 'Application',
        'fr': 'Application',
        'es': 'Aplicación',
        'ro': 'Aplicație',
    },
    'select-application-placeholder': {
        'en': 'Select an application…',
        'fr': 'Sélectionnez une application…',
        'es': 'Selecciona una aplicación…',
        'ro': 'Selectați o aplicație…',
    },
    'select-application-to-see-fields': {
        'en': 'Please select an application to get started.',
        'fr': 'Veuillez sélectionner une application pour commencer.',
        'es': 'Selecciona una aplicación para comenzar.',
        'ro': 'Selectați o aplicație pentru a începe.',
    },
    'select-entity': {
        'en': 'Entity',
        'fr': 'Entité',
        'es': 'Entidad',
        'ro': 'Entitate',
    },
    'select-entity-placeholder': {
        'en': 'Select an entity…',
        'fr': 'Sélectionnez une entité…',
        'es': 'Selecciona una entidad…',
        'ro': 'Selectați o entitate…',
    },
    'select-entity-to-see-fields': {
        'en': 'Please select an entity to view its fields.',
        'fr': 'Veuillez sélectionner une entité pour voir ses champs.',
        'es': 'Selecciona una entidad para ver sus campos.',
        'ro': 'Selectați o entitate pentru a vedea câmpurile sale.',
    },
    # --- Errors ---
    'not-exists': {
        'en': 'Record not found.',
        'fr': 'Enregistrement introuvable.',
        'es': 'Registro no encontrado.',
        'ro': 'Înregistrarea nu există.',
    },
}


class Command(BaseCommand):
    help = 'Seed all translation namespaces into the i18n database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Overwrite existing translation texts (default: skip existing).',
        )
        parser.add_argument(
            '--ns',
            type=str,
            default=None,
            help='Seed only a specific namespace (e.g. --ns generator).',
        )

    def handle(self, *args, **options):
        update = options['update']
        only_ns = options['ns']
        all_ns = set(TRANSLATIONS) | set(NAMESPACE_LINKS)

        to_seed = {k: v for k, v in TRANSLATIONS.items()
                   if only_ns is None or k == only_ns}
        to_link = {k: v for k, v in NAMESPACE_LINKS.items()
                   if only_ns is None or k == only_ns}

        if only_ns and only_ns not in all_ns:
            self.stdout.write(self.style.ERROR(f'Unknown namespace: {only_ns}'))
            return

        total_keys = total_created = total_updated = total_skipped = total_linked = 0

        # ------------------------------------------------------------------ #
        # 1. Seed TRANSLATIONS (create keys + texts)
        # ------------------------------------------------------------------ #
        for ns_name, keys in to_seed.items():
            ns_obj, ns_created = TranslationNameSpace.objects.get_or_create(ns=ns_name)
            if ns_created:
                self.stdout.write(self.style.SUCCESS(f"  Created namespace '{ns_name}'"))
            else:
                self.stdout.write(f"  Namespace '{ns_name}' -- {len(keys)} keys")

            for key_str, translations in keys.items():
                existing_keys = TranslationKey.objects.filter(key=key_str)
                if existing_keys.count() > 1:
                    key_obj = existing_keys.first()
                    key_created = False
                else:
                    key_obj, key_created = TranslationKey.objects.get_or_create(key=key_str)
                if key_created:
                    total_keys += 1
                key_obj.ns.add(ns_obj)

                for lng, text in translations.items():
                    if not text:
                        continue
                    existing = TranslationText.objects.filter(key=key_obj, lng=lng).first()
                    if existing:
                        if update:
                            existing.text = text
                            existing.save()
                            total_updated += 1
                        else:
                            total_skipped += 1
                    else:
                        TranslationText.objects.create(key=key_obj, lng=lng, text=text)
                        total_created += 1

        # ------------------------------------------------------------------ #
        # 2. Process NAMESPACE_LINKS (link existing keys to new namespaces,
        #    no text is created or modified)
        # ------------------------------------------------------------------ #
        for ns_name, key_list in to_link.items():
            ns_obj, ns_created = TranslationNameSpace.objects.get_or_create(ns=ns_name)
            if ns_created:
                self.stdout.write(self.style.SUCCESS(f"  Created namespace '{ns_name}' (via links)"))
            for key_str in key_list:
                existing_keys = TranslationKey.objects.filter(key=key_str)
                if not existing_keys.exists():
                    self.stdout.write(self.style.WARNING(
                        f"  WARNING: key '{key_str}' not found — cannot link to '{ns_name}'"
                    ))
                    continue
                key_obj = existing_keys.first()
                key_obj.ns.add(ns_obj)
                total_linked += 1

        self.stdout.write(self.style.SUCCESS(
            'Done.\n'
            '  Keys created:   ' + str(total_keys) + '\n' +
            '  Texts created:  ' + str(total_created) + '\n' +
            '  Texts updated:  ' + str(total_updated) + '\n' +
            '  Texts skipped:  ' + str(total_skipped) + ' (run with --update to overwrite)\n' +
            '  Keys linked:    ' + str(total_linked)
        ))


# ===========================================================================
# add-on module namespaces (user / subscription / support) — auto-seeded
# ===========================================================================
TRANSLATIONS['login'] = {
    "account-deleted": {'en': "Account deleted", 'fr': "Compte supprimé", 'es': "Cuenta eliminada", 'ro': "Cont șters"},
    "account-not-activated": {'en': "Your account is not activated yet.", 'fr': "Votre compte n'est pas encore activé.", 'es': "Su cuenta aún no está activada.", 'ro': "Contul dvs. nu este încă activat."},
    "confirm-link-in-email": {'en': "Confirmation link sent to your email", 'fr': "Lien de confirmation envoyé à votre email", 'es': "Enlace de confirmación enviado a tu correo", 'ro': "Link de confirmare trimis pe email"},
    "email": {'en': "Email", 'fr': "Email", 'es': "Correo electrónico", 'ro': "Email"},
    "email-invalid": {'en': "Invalid email address", 'fr': "Adresse email invalide", 'es': "Dirección de correo inválida", 'ro': "Adresă de email invalidă"},
    "email-missing": {'en': "Email is required", 'fr': "Le courriel est requis", 'es': "El correo es obligatorio", 'ro': "Emailul este obligatoriu"},
    "empty-field": {'en': "This field cannot be empty", 'fr': "Ce champ ne peut pas être vide", 'es': "Este campo no puede estar vacío", 'ro': "Acest câmp nu poate fi gol"},
    "error-occured": {'en': "An error occurred", 'fr': "Une erreur est survenue", 'es': "Ha ocurrido un error", 'ro': "A apărut o eroare"},
    "fields-mandatory": {'en': "Fields marked with", 'fr': "Champs marqués", 'es': "Campos marcados", 'ro': "Câmpuri marcate"},
    "login-successfull": {'en': "Login successful", 'fr': "Connexion réussie", 'es': "Inicio de sesión exitoso", 'ro': "Autentificare reușită"},
    "max-length-exceeded": {'en': "Maximum length exceeded", 'fr': "Longueur maximale dépassée", 'es': "Longitud máxima excedida", 'ro': "Lungimea maximă depășită"},
    "no-account-register": {'en': "Don't have an account? Register", 'fr': "Pas de compte ? S'inscrire", 'es': "¿No tienes cuenta? Regístrate", 'ro': "Nu ai cont? Înregistrează-te"},
    "password": {'en': "Password", 'fr': "Mot de passe", 'es': "Contraseña", 'ro': "Parolă"},
    "password-missing": {'en': "Password is required", 'fr': "Le mot de passe est requis", 'es': "La contraseña es obligatoria", 'ro': "Parola este obligatorie"},
    "registration-success": {'en': "Registration successful", 'fr': "Inscription réussie", 'es': "Registro exitoso", 'ro': "Înregistrare reușită"},
    "remember-device": {'en': "Remember this device for 1 week", 'fr': "Se souvenir de cet appareil pendant 1 semaine", 'es': "Recordar este dispositivo durante 1 semana", 'ro': "Ține minte acest dispozitiv timp de 1 săptămână"},
    "reset-password": {'en': "Reset password", 'fr': "Réinitialiser le mot de passe", 'es': "Restablecer contraseña", 'ro': "Resetează parola"},
    "tfa-back": {'en': "Back", 'fr': "Retour", 'es': "Volver", 'ro': "Înapoi"},
    "tfa-code": {'en': "Security code", 'fr': "Code de sécurité", 'es': "Código de seguridad", 'ro': "Cod de securitate"},
    "tfa-code-expired": {'en': "TFA code has expired, please request a new one", 'fr': "Le code TFA a expiré, veuillez en demander un nouveau", 'es': "El código TFA ha expirado, por favor solicita uno nuevo", 'ro': "Codul TFA a expirat, te rugăm să ceri unul nou"},
    "tfa-code-invalid": {'en': "Invalid TFA code", 'fr': "Code TFA invalide", 'es': "Código TFA inválido", 'ro': "Cod TFA invalid"},
    "tfa-code-required": {'en': "TFA code is required", 'fr': "Le code TFA est requis", 'es': "Se requiere código TFA", 'ro': "Codul TFA este obligatoriu"},
    "tfa-code-sent": {'en': "TFA code sent to your email", 'fr': "Code TFA envoyé à votre email", 'es': "Código TFA enviado a tu correo", 'ro': "Codul TFA a fost trimis pe email"},
    "tfa-enter-code": {'en': "Enter the code sent to your email", 'fr': "Entrez le code envoyé à votre email", 'es': "Ingrese el código enviado a su correo", 'ro': "Introdu codul trimis pe email"},
    "tfa-max-attempts": {'en': "Too many attempts, please request a new TFA code", 'fr': "Trop de tentatives, veuillez demander un nouveau code TFA", 'es': "Demasiados intentos, por favor solicita un nuevo código TFA", 'ro': "Prea multe încercări, te rugăm să ceri un nou cod TFA"},
    "tfa-resend-code": {'en': "Resend code", 'fr': "Renvoyer le code", 'es': "Reenviar código", 'ro': "Retrimite codul"},
    "tfa-resend-rate-limit": {'en': "Please wait before requesting a new TFA code", 'fr': "Veuillez attendre avant de demander un nouveau code TFA", 'es': "Por favor espera antes de solicitar un nuevo código TFA", 'ro': "Te rugăm să aștepți înainte de a cere un nou cod TFA"},
    "user-unknown-or-wrong-credentials": {'en': "Unknown user or wrong credentials", 'fr': "Utilisateur inconnu ou identifiants incorrects", 'es': "Usuario desconocido o credenciales incorrectas", 'ro': "Utilizator necunoscut sau credențiale incorecte"},
    "validate": {'en': "Validate", 'fr': "Valider", 'es': "Validar", 'ro': "Validează"},
}

TRANSLATIONS['register'] = {
    "download-cgu": {'en': "Download the terms and conditions", 'fr': "Télécharger les conditions générales", 'es': "Descargar los términos y condiciones", 'ro': "Descărcați termenii și condițiile"},
    "link-to-cgu": {'en': "I accept the terms and conditions", 'fr': "J'accepte les conditions générales", 'es': "Acepto los términos y condiciones", 'ro': "Accept termenii și condițiile"},
    "register": {'en': "Register", 'fr': "S'inscrire", 'es': "Registrarse", 'ro': "Înregistrare"},
}

TRANSLATIONS['profile'] = {
    "confirm-remove-profile": {'en': "Are you sure you want to delete your profile?", 'fr': "Êtes-vous sûr de vouloir supprimer votre profil ?", 'es': "¿Está seguro de que desea eliminar su perfil?", 'ro': "Sigur doriți să vă ștergeți profilul?"},
    "delete-profile": {'en': "Delete profile", 'fr': "Supprimer le profil", 'es': "Eliminar perfil", 'ro': "Șterge profilul"},
    "password-change": {'en': "Change password", 'fr': "Changer le mot de passe", 'es': "Cambiar la contraseña", 'ro': "Schimbă parola"},
    "profile": {'en': "Profile", 'fr': "Profil", 'es': "Perfil", 'ro': "Profil"},
    "remove-profile-subscription-text": {'en': "Deleting your profile will also cancel your active subscription.", 'fr': "La suppression de votre profil annulera également votre abonnement actif.", 'es': "Eliminar su perfil también cancelará su suscripción activa.", 'ro': "Ștergerea profilului va anula și abonamentul activ."},
    "remove-profile-text": {'en': "This action is irreversible and will permanently delete your account.", 'fr': "Cette action est irréversible et supprimera définitivement votre compte.", 'es': "Esta acción es irreversible y eliminará permanentemente su cuenta.", 'ro': "Această acțiune este ireversibilă și vă va șterge definitiv contul."},
    "your-informations": {'en': "Your information", 'fr': "Vos informations", 'es': "Su información", 'ro': "Informațiile dvs."},
}

TRANSLATIONS['password'] = {
    "change-password": {'en': "Password change", 'fr': "Changement de mot de passe", 'es': "Cambio de contraseña", 'ro': "Schimbare parolă"},
    "confirm-password": {'en': "Confirm password", 'fr': "Confirmer le mot de passe", 'es': "Confirmar contraseña", 'ro': "Confirmați parola"},
    "empty-field": {'en': "This field cannot be empty", 'fr': "Ce champ ne peut pas être vide", 'es': "Este campo no puede estar vacío", 'ro': "Acest câmp nu poate fi gol"},
    "error-occured": {'en': "An error occurred", 'fr': "Une erreur est survenue", 'es': "Ha ocurrido un error", 'ro': "A apărut o eroare"},
    "fields-mandatory": {'en': "Fields marked with", 'fr': "Champs marqués", 'es': "Campos marcados", 'ro': "Câmpuri marcate"},
    "old-password": {'en': "Current password", 'fr': "Mot de passe actuel", 'es': "Contraseña actual", 'ro': "Parola curentă"},
    "password": {'en': "Password", 'fr': "Mot de passe", 'es': "Contraseña", 'ro': "Parolă"},
    "password-length": {'en': "At least 8 characters", 'fr': "Au moins 8 caractères", 'es': "Al menos 8 caracteres", 'ro': "Cel puțin 8 caractere"},
    "password-lowercase": {'en': "At least one lowercase letter", 'fr': "Au moins une lettre minuscule", 'es': "Al menos una letra minúscula", 'ro': "Cel puțin o literă mică"},
    "password-match": {'en': "Passwords match", 'fr': "Les mots de passe correspondent", 'es': "Las contraseñas coinciden", 'ro': "Parolele se potrivesc"},
    "password-number": {'en': "At least one number", 'fr': "Au moins un chiffre", 'es': "Al menos un número", 'ro': "Cel puțin o cifră"},
    "password-special-characters": {'en': "At least one special character", 'fr': "Au moins un caractère spécial", 'es': "Al menos un carácter especial", 'ro': "Cel puțin un caracter special"},
    "password-uppercase": {'en': "At least one uppercase letter", 'fr': "Au moins une lettre majuscule", 'es': "Al menos una letra mayúscula", 'ro': "Cel puțin o literă mare"},
    "token": {'en': "token", 'fr': "token", 'es': "token", 'ro': "token"},
    "uidb64": {'en': "uidb64", 'fr': "uidb64", 'es': "uidb64", 'ro': "uidb64"},
    "validate": {'en': "Validate", 'fr': "Valider", 'es': "Validar", 'ro': "Validează"},
}

TRANSLATIONS['reset'] = {
    "email": {'en': "Email", 'fr': "Email", 'es': "Correo electrónico", 'ro': "Email"},
    "email-invalid": {'en': "Invalid email address", 'fr': "Adresse email invalide", 'es': "Dirección de correo inválida", 'ro': "Adresă de email invalidă"},
    "error-occured": {'en': "An error occurred", 'fr': "Une erreur est survenue", 'es': "Ha ocurrido un error", 'ro': "A apărut o eroare"},
    "fields-mandatory": {'en': "Fields marked with", 'fr': "Champs marqués", 'es': "Campos marcados", 'ro': "Câmpuri marcate"},
    "help-change-password": {'en': "Enter your email and we'll send you a link to reset your password.", 'fr': "Saisissez votre courriel et nous vous enverrons un lien pour réinitialiser votre mot de passe.", 'es': "Introduzca su correo y le enviaremos un enlace para restablecer su contraseña.", 'ro': "Introduceți emailul și vă vom trimite un link pentru resetarea parolei."},
    "reset-password": {'en': "Reset password", 'fr': "Réinitialiser le mot de passe", 'es': "Restablecer contraseña", 'ro': "Resetează parola"},
    "validate": {'en': "Validate", 'fr': "Valider", 'es': "Validar", 'ro': "Validează"},
}

TRANSLATIONS['invitation'] = {
    "complete-invitation": {'en': "Complete your invitation", 'fr': "Compléter votre invitation", 'es': "Complete su invitación", 'ro': "Finalizați invitația"},
    "id": {'en': "id", 'fr': "id", 'es': "id", 'ro': "id"},
    "token": {'en': "token", 'fr': "token", 'es': "token", 'ro': "token"},
    "uidb64": {'en': "uidb64", 'fr': "uidb64", 'es': "uidb64", 'ro': "uidb64"},
}

TRANSLATIONS['userform'] = {
    "accept-cgu": {'en': "I accept the terms and conditions", 'fr': "J'accepte les conditions générales", 'es': "Acepto los términos y condiciones", 'ro': "Accept termenii și condițiile"},
    "address": {'en': "Address", 'fr': "Adresse", 'es': "Dirección", 'ro': "Adresă"},
    "ask-to-change-email": {'en': "To change your email, please contact support.", 'fr': "Pour modifier votre courriel, veuillez contacter le support.", 'es': "Para cambiar su correo, contacte con soporte.", 'ro': "Pentru a schimba emailul, contactați asistența."},
    "city": {'en': "City", 'fr': "Ville", 'es': "Ciudad", 'ro': "Oraș"},
    "company-name": {'en': "Company name", 'fr': "Nom de l'entreprise", 'es': "Nombre de la empresa", 'ro': "Numele companiei"},
    "confirm-password": {'en': "Confirm password", 'fr': "Confirmer le mot de passe", 'es': "Confirmar contraseña", 'ro': "Confirmați parola"},
    "country": {'en': "Country", 'fr': "Pays", 'es': "País", 'ro': "Țară"},
    "email": {'en': "Email", 'fr': "Email", 'es': "Correo electrónico", 'ro': "Email"},
    "email-invalid": {'en': "Invalid email address", 'fr': "Adresse email invalide", 'es': "Dirección de correo inválida", 'ro': "Adresă de email invalidă"},
    "error-occured": {'en': "An error occurred", 'fr': "Une erreur est survenue", 'es': "Ha ocurrido un error", 'ro': "A apărut o eroare"},
    "fields-mandatory": {'en': "Fields marked with", 'fr': "Champs marqués", 'es': "Campos marcados", 'ro': "Câmpuri marcate"},
    "first_name": {'en': "First name", 'fr': "Prénom", 'es': "Nombre", 'ro': "Prenume"},
    "last_name": {'en': "Last name", 'fr': "Nom", 'es': "Apellido", 'ro': "Nume"},
    "modify": {'en': "Edit", 'fr': "Modifier", 'es': "Modificar", 'ro': "Modifică"},
    "password": {'en': "Password", 'fr': "Mot de passe", 'es': "Contraseña", 'ro': "Parolă"},
    "professional": {'en': "Professional", 'fr': "Professionnel", 'es': "Profesional", 'ro': "Profesional"},
    "select-country": {'en': "Select a country", 'fr': "Sélectionnez un pays", 'es': "Seleccione un país", 'ro': "Selectați o țară"},
    "taxnumber": {'en': "VAT number", 'fr': "Numéro de TVA", 'es': "Número de IVA", 'ro': "Cod TVA"},
    "validate": {'en': "Validate", 'fr': "Valider", 'es': "Validar", 'ro': "Validează"},
    "zipcode": {'en': "Postal code", 'fr': "Code postal", 'es': "Código postal", 'ro': "Cod poștal"},
}

TRANSLATIONS['upload'] = {
    "error-occured": {'en': "An error occurred", 'fr': "Une erreur est survenue", 'es': "Ha ocurrido un error", 'ro': "A apărut o eroare"},
    "select-file": {'en': "Select file", 'fr': "Sélectionner un fichier", 'es': "Seleccionar archivo", 'ro': "Selectează fișier"},
    "upload": {'en': "Upload", 'fr': "Télécharger", 'es': "Subir", 'ro': "Încărcare"},
    "upload-file": {'en': "Upload file", 'fr': "Télécharger un fichier", 'es': "Subir archivo", 'ro': "Încărcare fișier"},
    "upload-support-help": {'en': "You can upload images, PDFs or documents (max 10MB)", 'fr': "Vous pouvez télécharger des images, PDF ou documents (max 10Mo)", 'es': "Puede subir imágenes, PDF o documentos (máx 10MB)", 'ro': "Puteți încărca imagini, PDF sau documente (max 10MB)"},
}

TRANSLATIONS['subscription'] = {
    "DD-MM-y": {'en': "DD-MM-YYYY", 'fr': "DD-MM-YYYY", 'es': "DD-MM-YYYY", 'ro': "DD-MM-YYYY"},
    "DD-MM-y HH:mm:ss": {'en': "DD-MM-YYYY HH:mm:ss", 'fr': "DD-MM-YYYY HH:mm:ss", 'es': "DD-MM-YYYY HH:mm:ss", 'ro': "DD-MM-YYYY HH:mm:ss"},
    "accepted-cards": {'en': "Accepted cards", 'fr': "Cartes acceptées", 'es': "Tarjetas aceptadas", 'ro': "Carduri acceptate"},
    "access-until": {'en': "Access until", 'fr': "Accès jusqu'au", 'es': "Acceso hasta", 'ro': "Acces până la"},
    "automatic-renewal-at": {'en': "Automatic renewal on", 'fr': "Renouvellement automatique le", 'es': "Renovación automática el", 'ro': "Reînnoire automată la"},
    "cancelled-subscription": {'en': "Cancelled subscription", 'fr': "Abonnement annulé", 'es': "Suscripción cancelada", 'ro': "Abonament anulat"},
    "change-subscription": {'en': "Change subscription", 'fr': "Changer d'abonnement", 'es': "Cambiar suscripción", 'ro': "Schimbă abonamentul"},
    "confirm-change-subscription": {'en': "Confirm subscription change", 'fr': "Confirmer le changement d'abonnement", 'es': "Confirmar cambio de suscripción", 'ro': "Confirmați schimbarea abonamentului"},
    "confirm-reactivate-subscription": {'en': "Confirm subscription reactivation", 'fr': "Confirmer la réactivation de l'abonnement", 'es': "Confirmar la reactivación de la suscripción", 'ro': "Confirmați reactivarea abonamentului"},
    "confirm-unsubscribe": {'en': "Confirm cancellation", 'fr': "Confirmer la résiliation", 'es': "Confirmar la cancelación", 'ro': "Confirmați anularea"},
    "current-subscription": {'en': "Current subscription", 'fr': "Abonnement actuel", 'es': "Suscripción actual", 'ro': "Abonament curent"},
    "download-invoice": {'en': "Download invoice", 'fr': "Télécharger la facture", 'es': "Descargar factura", 'ro': "Descarcă factura"},
    "first-payment-at": {'en': "First payment on", 'fr': "Premier paiement le", 'es': "Primer pago el", 'ro': "Prima plată la"},
    "help-change-subscription": {'en': "Choose a new plan below to change your subscription.", 'fr': "Choisissez un nouveau forfait ci-dessous pour changer d'abonnement.", 'es': "Elija un nuevo plan a continuación para cambiar su suscripción.", 'ro': "Alegeți un plan nou mai jos pentru a schimba abonamentul."},
    "help-confirm-reactivate-subscription": {'en': "Your subscription will be reactivated and billing will resume.", 'fr': "Votre abonnement sera réactivé et la facturation reprendra.", 'es': "Su suscripción se reactivará y la facturación se reanudará.", 'ro': "Abonamentul va fi reactivat și facturarea va fi reluată."},
    "help-confirm-unsubscribe": {'en': "Your subscription will remain active until the end of the current period.", 'fr': "Votre abonnement restera actif jusqu'à la fin de la période en cours.", 'es': "Su suscripción permanecerá activa hasta el final del período actual.", 'ro': "Abonamentul va rămâne activ până la sfârșitul perioadei curente."},
    "label": {'en': "Label", 'fr': "Libellé", 'es': "Etiqueta", 'ro': "Etichetă"},
    "no-plans-for-the-moment": {'en': "No plans available at the moment.", 'fr': "Aucun forfait disponible pour le moment.", 'es': "No hay planes disponibles por el momento.", 'ro': "Niciun plan disponibil momentan."},
    "no-subscription": {'en': "No subscription", 'fr': "Aucun abonnement", 'es': "Sin suscripción", 'ro': "Fără abonament"},
    "normal-subscription": {'en': "Standard subscription", 'fr': "Abonnement standard", 'es': "Suscripción estándar", 'ro': "Abonament standard"},
    "of": {'en': "of", 'fr': "de", 'es': "de", 'ro': "din"},
    "paid": {'en': "Paid", 'fr': "Payé", 'es': "Pagado", 'ro': "Plătit"},
    "pay": {'en': "Pay", 'fr': "Payer", 'es': "Pagar", 'ro': "Plătește"},
    "plan": {'en': "Plan", 'fr': "Forfait", 'es': "Plan", 'ro': "Plan"},
    "plans": {'en': "Plans", 'fr': "Forfaits", 'es': "Planes", 'ro': "Planuri"},
    "price": {'en': "Price", 'fr': "Prix", 'es': "Precio", 'ro': "Preț"},
    "pricing": {'en': "Pricing", 'fr': "Tarifs", 'es': "Precios", 'ro': "Prețuri"},
    "proceed-to-payment": {'en': "Proceed to payment", 'fr': "Procéder au paiement", 'es': "Proceder al pago", 'ro': "Continuați la plată"},
    "reactivate-subscription": {'en': "Reactivate subscription", 'fr': "Réactiver l'abonnement", 'es': "Reactivar la suscripción", 'ro': "Reactivează abonamentul"},
    "secure-payment": {'en': "Secure payment", 'fr': "Paiement sécurisé", 'es': "Pago seguro", 'ro': "Plată securizată"},
    "secure-zone": {'en': "Secure area", 'fr': "Zone sécurisée", 'es': "Zona segura", 'ro': "Zonă securizată"},
    "select-plan": {'en': "Select a plan", 'fr': "Sélectionnez un forfait", 'es': "Seleccione un plan", 'ro': "Selectați un plan"},
    "stripe-powered": {'en': "Powered by Stripe", 'fr': "Propulsé par Stripe", 'es': "Con tecnología de Stripe", 'ro': "Susținut de Stripe"},
    "subscribe": {'en': "Subscribe", 'fr': "S'abonner", 'es': "Suscribirse", 'ro': "Abonează-te"},
    "subscription-error": {'en': "An error occurred with your subscription.", 'fr': "Une erreur est survenue avec votre abonnement.", 'es': "Se produjo un error con su suscripción.", 'ro': "A apărut o eroare cu abonamentul dvs."},
    "subscription-success": {'en': "Your subscription was successful.", 'fr': "Votre abonnement a réussi.", 'es': "Su suscripción se realizó con éxito.", 'ro': "Abonamentul a fost realizat cu succes."},
    "trial-explanation": {'en': "Try free for the trial period, cancel anytime.", 'fr': "Essayez gratuitement pendant la période d'essai, annulez à tout moment.", 'es': "Pruebe gratis durante el período de prueba, cancele cuando quiera.", 'ro': "Încercați gratuit în perioada de probă, anulați oricând."},
    "trial-period": {'en': "Trial period", 'fr': "Période d'essai", 'es': "Período de prueba", 'ro': "Perioadă de probă"},
    "trial-subscription": {'en': "Trial subscription", 'fr': "Abonnement d'essai", 'es': "Suscripción de prueba", 'ro': "Abonament de probă"},
    "try": {'en': "Try", 'fr': "Essayer", 'es': "Probar", 'ro': "Încearcă"},
    "ttc": {'en': "incl. tax", 'fr': "TTC", 'es': "imp. incl.", 'ro': "cu TVA"},
    "unpaid": {'en': "Unpaid", 'fr': "Impayé", 'es': "No pagado", 'ro': "Neplătit"},
    "unsubscribe": {'en': "Cancel subscription", 'fr': "Résilier l'abonnement", 'es': "Cancelar suscripción", 'ro': "Anulează abonamentul"},
    "validate": {'en': "Validate", 'fr': "Valider", 'es': "Validar", 'ro': "Validează"},
    "vat": {'en': "VAT", 'fr': "TVA", 'es': "IVA", 'ro': "TVA"},
    "with-trial": {'en': "with trial", 'fr': "avec essai", 'es': "con prueba", 'ro': "cu probă"},
    "your-invoices": {'en': "Your invoices", 'fr': "Vos factures", 'es': "Sus facturas", 'ro': "Facturile dvs."},
    "your-subscription": {'en': "Your subscription", 'fr': "Votre abonnement", 'es': "Su suscripción", 'ro': "Abonamentul dvs."},
}

TRANSLATIONS['support'] = {
    "DD-MM-YYYY HH:mm:ss": {'en': "DD-MM-YYYY HH:mm:ss", 'fr': "DD-MM-YYYY HH:mm:ss", 'es': "DD-MM-YYYY HH:mm:ss", 'ro': "DD-MM-YYYY HH:mm:ss"},
    "DD-MM-y": {'en': "DD-MM-YYYY", 'fr': "DD-MM-YYYY", 'es': "DD-MM-YYYY", 'ro': "DD-MM-YYYY"},
    "add-ticket": {'en': "Add ticket", 'fr': "Ajouter un ticket", 'es': "Añadir ticket", 'ro': "Adaugă ticket"},
    "close": {'en': "Close", 'fr': "Fermer", 'es': "Cerrar", 'ro': "Închide"},
    "closed-tickets": {'en': "Closed tickets", 'fr': "Tickets fermés", 'es': "Tickets cerrados", 'ro': "Tichete închise"},
    "confirm-close-ticket": {'en': "Are you sure you want to close this ticket?", 'fr': "Êtes-vous sûr de vouloir fermer ce ticket ?", 'es': "¿Está seguro de que desea cerrar este ticket?", 'ro': "Sigur doriți să închideți acest tichet?"},
    "contact": {'en': "Contact", 'fr': "Contact", 'es': "Contacto", 'ro': "Contact"},
    "content": {'en': "Content", 'fr': "Contenu", 'es': "Contenido", 'ro': "Conținut"},
    "creation-date": {'en': "Created on", 'fr': "Date de création", 'es': "Fecha de creación", 'ro': "Data creării"},
    "discussion": {'en': "Discussion", 'fr': "Discussion", 'es': "Discusión", 'ro': "Discuție"},
    "download-file": {'en': "Download file", 'fr': "Télécharger le fichier", 'es': "Descargar archivo", 'ro': "Descarcă fișierul"},
    "edit": {'en': "Modify", 'fr': "Modifier", 'es': "Modificar", 'ro': "Modifică"},
    "email": {'en': "Email", 'fr': "Email", 'es': "Correo electrónico", 'ro': "Email"},
    "error-occured": {'en': "An error occurred", 'fr': "Une erreur est survenue", 'es': "Ha ocurrido un error", 'ro': "A apărut o eroare"},
    "free-topic": {'en': "Other topic", 'fr': "Sujet libre", 'es': "Tema libre", 'ro': "Subiect liber"},
    "id": {'en': "id", 'fr': "id", 'es': "id", 'ro': "id"},
    "message-from-you": {'en': "Your message", 'fr': "Message de votre part", 'es': "Su mensaje", 'ro': "Mesajul dvs."},
    "modification-date": {'en': "Updated on", 'fr': "Date de modification", 'es': "Fecha de modificación", 'ro': "Data modificării"},
    "no-opened-ticket-yet-create-one": {'en': "No open tickets yet — create one.", 'fr': "Aucun ticket ouvert pour le moment — créez-en un.", 'es': "Aún no hay tickets abiertos: cree uno.", 'ro': "Niciun tichet deschis încă — creați unul."},
    "no-ticket-yet-create-one": {'en': "No ticket yet, create one", 'fr': "Pas encore de ticket, créez-en un", 'es': "Aún no hay ticket, crea uno", 'ro': "Încă nu există ticket, creează unul"},
    "number": {'en': "Number", 'fr': "Numéro", 'es': "Número", 'ro': "Număr"},
    "open-tickets": {'en': "Open tickets", 'fr': "Tickets ouverts", 'es': "Tickets abiertos", 'ro': "Tichete deschise"},
    "other-topic": {'en': "Other", 'fr': "Autre", 'es': "Otro", 'ro': "Altul"},
    "our-answer": {'en': "Our answer", 'fr': "Notre réponse", 'es': "Nuestra respuesta", 'ro': "Răspunsul nostru"},
    "select-topic": {'en': "Select a topic", 'fr': "Sélectionnez un sujet", 'es': "Seleccione un tema", 'ro': "Selectați un subiect"},
    "topic": {'en': "Topic", 'fr': "Sujet", 'es': "Tema", 'ro': "Subiect"},
    "update-thread": {'en': "Update message", 'fr': "Mettre à jour le message", 'es': "Actualizar mensaje", 'ro': "Actualizează mesajul"},
    "update-ticket": {'en': "Update ticket", 'fr': "Mettre à jour le ticket", 'es': "Actualizar ticket", 'ro': "Actualizează tichetul"},
    "upload-file": {'en': "Upload file", 'fr': "Télécharger un fichier", 'es': "Subir archivo", 'ro': "Încărcare fișier"},
    "validate": {'en': "Validate", 'fr': "Valider", 'es': "Validar", 'ro': "Validează"},
    "your-tickets": {'en': "Your tickets", 'fr': "Vos tickets", 'es': "Sus tickets", 'ro': "Tiketurile tale"},
}

TRANSLATIONS['email']['tfa-email-subject'] = {'en': "Your security code", 'fr': "Votre code de sécurité", 'es': "Tu código de seguridad", 'ro': "Codul tău de securitate"}
