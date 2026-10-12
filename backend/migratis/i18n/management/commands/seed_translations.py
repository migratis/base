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

# common/components/InvoiceList renders under the shared `billing` namespace so
# either monetization module can list its own receipts. The invoice-line wording
# was written for the subscription block and stays owned there.
NAMESPACE_LINKS['billing'] = [
    'your-invoices', 'download-invoice', 'paid', 'unpaid', 'of', 'trial-period',
]

# The /cookies page title is the footer label that links to it, so a link and
# the page it opens cannot disagree.
NAMESPACE_LINKS['cookie'] = ['cookies', 'privacy-policy']


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
    # Accessible name of the floating button that opens and closes the menu on
    # a narrow screen (Layout.js).
    'toggle-menu': {
        'en': 'Open or close the menu',
        'fr': 'Ouvrir ou fermer le menu',
        'es': 'Abrir o cerrar el menú',
        'ro': 'Deschide sau închide meniul',
    },
    'access-denied': {
        'en': 'Access denied',
        'fr': 'Accès refusé',
        'es': 'Acceso denegado',
        'ro': 'Acces interzis',
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
        'fr': "Documentation du Générateur d'Applications",
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
    'contact': {
        'en': 'Contact',
        'fr': 'Contact',
        'es': 'Contacto',
        'ro': 'Contact',
    },
    'home': {
        'en': 'Home',
        'fr': 'Accueil',
        'es': 'Inicio',
        'ro': 'Acasă',
    },
    # NOTE: the landing-page copy (hero / chapter / CTA keys) lives in the
    # `home` namespace only — TranslationKey rows are global, so duplicating
    # them here just made two sources of truth for the same texts.
    'logout': {
        'en': 'Logout',
        'fr': 'Déconnexion',
        'es': 'Cerrar sesión',
        'ro': 'Deconectare',
    },
    # Returned by GET /user/logout and toasted by Header / MenuLeft.
    'logout-successfully': {
        'en': 'You have been logged out.',
        'fr': 'Vous avez été déconnecté.',
        'es': 'Has cerrado sesión.',
        'ro': 'Ai fost deconectat.',
    },
    'login': {
        'en': 'Login',
        'fr': 'Se connecter',
        'es': 'Iniciar sesión',
        'ro': 'Autentificare',
    },
    'tfa-enter-code': {
        'en': 'Enter the code sent to your email',
        'fr': 'Entrez le code envoyé à votre email',
        'es': 'Ingrese el código enviado a su correo',
        'ro': 'Introdu codul trimis pe email',
    },
    'tfa-code': {
        'en': 'Security code',
        'fr': 'Code de sécurité',
        'es': 'Código de seguridad',
        'ro': 'Cod de securitate',
    },
    'tfa-resend-code': {
        'en': 'Resend code',
        'fr': 'Renvoyer le code',
        'es': 'Reenviar código',
        'ro': 'Retrimite codul',
    },
    'tfa-back': {
        'en': 'Back',
        'fr': 'Retour',
        'es': 'Volver',
        'ro': 'Înapoi',
    },
    'tfa-code-required': {
        'en': 'TFA code is required',
        'fr': 'Le code TFA est requis',
        'es': 'Se requiere código TFA',
        'ro': 'Codul TFA este obligatoriu',
    },
    'tfa-code-invalid': {
        'en': 'Invalid TFA code',
        'fr': 'Code TFA invalide',
        'es': 'Código TFA inválido',
        'ro': 'Cod TFA invalid',
    },
    'tfa-code-expired': {
        'en': 'TFA code has expired, please request a new one',
        'fr': 'Le code TFA a expiré, veuillez en demander un nouveau',
        'es': 'El código TFA ha expirado, por favor solicita uno nuevo',
        'ro': 'Codul TFA a expirat, te rugăm să ceri unul nou',
    },
    'tfa-max-attempts': {
        'en': 'Too many attempts, please request a new TFA code',
        'fr': 'Trop de tentatives, veuillez demander un nouveau code TFA',
        'es': 'Demasiados intentos, por favor solicita un nuevo código TFA',
        'ro': 'Prea multe încercări, te rugăm să ceri un nou cod TFA',
    },
    'tfa-code-sent': {
        'en': 'TFA code sent to your email',
        'fr': 'Code TFA envoyé à votre email',
        'es': 'Código TFA enviado a tu correo',
        'ro': 'Codul TFA a fost trimis pe email',
    },
    'tfa-resend-rate-limit': {
        'en': 'Please wait before requesting a new TFA code',
        'fr': 'Veuillez attendre avant de demander un nouveau code TFA',
        'es': 'Por favor espera antes de solicitar un nuevo código TFA',
        'ro': 'Te rugăm să aștepți înainte de a cere un nou cod TFA',
    },
    'remember-device': {
        'en': 'Remember this device for 1 week',
        'fr': 'Se souvenir de cet appareil pendant 1 semaine',
        'es': 'Recordar este dispositivo durante 1 semana',
        'ro': 'Ține minte acest dispozitiv timp de 1 săptămână',
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
    'account-settings': {
        'en': 'Account settings',
        'fr': 'Paramètres du compte',
        'es': 'Configuración de la cuenta',
        'ro': 'Setări cont',
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
    'your-tickets': {
        'en': 'Your tickets',
        'fr': 'Vos tickets',
        'es': 'Sus tickets',
        'ro': 'Tiketurile tale',
    },
    'add-ticket': {
        'en': 'Add ticket',
        'fr': 'Ajouter un ticket',
        'es': 'Añadir ticket',
        'ro': 'Adaugă ticket',
    },
    'no-ticket-yet-create-one': {
        'en': 'No ticket yet, create one',
        'fr': 'Pas encore de ticket, créez-en un',
        'es': 'Aún no hay ticket, crea uno',
        'ro': 'Încă nu există ticket, creează unul',
    },
    'upload': {
        'en': 'Upload',
        'fr': 'Télécharger',
        'es': 'Subir',
        'ro': 'Încărcare',
    },
    'upload-file': {
        'en': 'Upload file',
        'fr': 'Télécharger un fichier',
        'es': 'Subir archivo',
        'ro': 'Încărcare fișier',
    },
    'select-file': {
        'en': 'Select file',
        'fr': 'Sélectionner un fichier',
        'es': 'Seleccionar archivo',
        'ro': 'Selectează fișier',
    },
    'upload-support-help': {
        'en': 'You can upload images, PDFs or documents (max 10MB)',
        'fr': 'Vous pouvez télécharger des images, PDF ou documents (max 10Mo)',
        'es': 'Puede subir imágenes, PDF o documentos (máx 10MB)',
        'ro': 'Puteți încărca imagini, PDF sau documente (max 10MB)',
    },
    'session-expired': {
        'en': 'Session Expired',
        'fr': 'Session Expirée',
        'es': 'Sesión Expirada',
        'ro': 'Sesiune Expirată',
    },
    # Cookie consent banner (CookieConsent.js, ns 'layout').

}

# ===========================================================================
# Footer labels (layout)
# ===========================================================================
# The footer rendered raw slugs — none of its own labels had ever been seeded.
# These are the short strings; the pages behind the links carry their prose in
# the `legal` and `info` namespaces below.
TRANSLATIONS['layout'].update({
    # NOTE: the footer's "About" and "Services" panes were removed — they
    # restated the home page in the one band nobody reads prose in, and squeezed
    # the links into a third of the width. Their keys (`about`, `text-about`,
    # `other-services`, `text-other-services`) are gone with them.
    'informations': {
        'en': 'Information',
        'fr': 'Informations',
        'es': 'Información',
        'ro': 'Informații',
    },
    'text-informations': {
        'en': 'Support, documentation and the legal terms of the service.',
        'fr': 'Support, documentation et conditions légales du service.',
        'es': 'Soporte, documentación y condiciones legales del servicio.',
        'ro': 'Suport, documentație și condițiile legale ale serviciului.',
    },
    'help': {
        'en': 'Help',
        'fr': 'Aide',
        'es': 'Ayuda',
        'ro': 'Ajutor',
    },
    'legal': {
        'en': 'Legal',
        'fr': 'Légal',
        'es': 'Legal',
        'ro': 'Juridic',
    },
    'legal-notice': {
        'en': 'Legal notice',
        'fr': 'Mentions légales',
        'es': 'Aviso legal',
        'ro': 'Mențiuni legale',
    },
    'legal-disclaimer': {
        'en': 'Legal disclaimer',
        'fr': 'Avertissement légal',
        'es': 'Limitación de responsabilidad',
        'ro': 'Declinarea responsabilității',
    },
    'terms-of-service': {
        'en': 'Terms of sale',
        'fr': 'Conditions générales de vente',
        'es': 'Condiciones generales de venta',
        'ro': 'Condiții generale de vânzare',
    },
    'privacy-policy': {
        'en': 'Privacy policy',
        'fr': 'Politique de confidentialité',
        'es': 'Política de privacidad',
        'ro': 'Politica de confidențialitate',
    },
    'refund-policy': {
        'en': 'Refunds & withdrawal',
        'fr': 'Remboursement et rétractation',
        'es': 'Reembolsos y desistimiento',
        'ro': 'Rambursări și retragere',
    },
    'licensing': {
        'en': 'Open-source licensing',
        'fr': 'Licence open source',
        'es': 'Licencia de código abierto',
        'ro': 'Licențiere open-source',
    },
    'security': {
        'en': 'Security',
        'fr': 'Sécurité',
        'es': 'Seguridad',
        'ro': 'Securitate',
    },
    'status': {
        'en': 'Service status',
        'fr': 'État du service',
        'es': 'Estado del servicio',
        'ro': 'Starea serviciului',
    },
    # Footer label *and* the title of the page it opens (linked into `info` via
    # NAMESPACE_LINKS), so the two can never disagree.
    'llm-providers': {
        'en': 'List your AI model',
        'fr': 'Référencer votre modèle IA',
        'es': 'Publica tu modelo de IA',
        'ro': 'Listează-ți modelul AI',
    },
    'cookies': {
        'en': 'Cookies',
        'fr': 'Cookies',
        'es': 'Cookies',
        'ro': 'Cookie-uri',
    },
    'all-rights-reserved': {
        'en': 'Migratis — all rights reserved.',
        'fr': 'Migratis — tous droits réservés.',
        'es': 'Migratis — todos los derechos reservados.',
        'ro': 'Migratis — toate drepturile rezervate.',
    },
    # The whole of this template's footer (common/components/Footer.js — the one
    # file migratis does not sync down, because an application built from the
    # framework is owned by somebody else and must not publish migratis.ai's
    # terms as its own). What is left is what is honestly ours to say: what this
    # runs on, and where its source is.
    'built-with-migratis': {
        'en': 'Built with Migratis',
        'fr': 'Propulsé par Migratis',
        'es': 'Creado con Migratis',
        'ro': 'Creat cu Migratis',
    },
    'source-code': {
        'en': 'Source code',
        'fr': 'Code source',
        'es': 'Código fuente',
        'ro': 'Codul sursă',
    },
})

# ===========================================================================
# cookie
# ===========================================================================
TRANSLATIONS['cookie'] = {
    # ── The /cookies page ───────────────────────────────────────────────────
    # The page title is the footer label (`cookies`, linked in from `layout`),
    # so a link and the page it opens cannot disagree. `cookies-list` was its
    # own wording and already did.
    'storage-intro': {
        'en': 'Everything this site stores on your device, what it is for, and how '
              'long it lasts. The list covers cookies and browser storage alike — '
              'the law treats them the same way.',
        'fr': "Tout ce que ce site conserve sur votre appareil, à quoi cela sert et "
              "combien de temps cela dure. La liste couvre les cookies comme le "
              "stockage du navigateur : la loi les traite de la même façon.",
        'es': 'Todo lo que este sitio almacena en su dispositivo, para qué sirve y '
              'cuánto dura. La lista cubre tanto las cookies como el almacenamiento '
              'del navegador: la ley los trata igual.',
        'ro': 'Tot ce stochează acest site pe dispozitivul dvs., la ce folosește și '
              'cât '
              'durează. Lista acoperă atât cookie-urile, cât și stocarea din '
              'browser — legea le tratează la fel.',
    },
    'your-choice': {
        'en': 'Your choice',
        'fr': 'Votre choix',
        'es': 'Su elección',
        'ro': 'Alegerea dvs.',
    },
    # The honest statement of this deployment's position, and the reason the
    # first-visit banner is a notice rather than a consent request.
    'nothing-to-consent-to': {
        'en': 'There is nothing here for you to accept or refuse. This site stores '
              'only what it needs to work — your session, the token that protects '
              'forms, the language you chose and the record of this notice — and '
              'runs no analytics, serves no advertising and loads no third-party '
              'tracking script. Storage of that kind is exempt from consent, so '
              'asking you for it would be misleading.',
        'fr': "Il n'y a rien ici à accepter ou à refuser. Ce site ne conserve que "
              "ce qui est nécessaire à son fonctionnement — votre session, le jeton "
              "qui protège les formulaires, la langue que vous avez choisie et la "
              "trace de cet avis — et n'utilise aucune mesure d'audience, aucune "
              "publicité et aucun script de suivi tiers. Ce type de stockage est "
              "exempté de consentement : vous le demander serait trompeur.",
        'es': 'Aquí no hay nada que aceptar o rechazar. Este sitio almacena solo lo '
              'que necesita para funcionar — su sesión, el token que protege los '
              'formularios, el idioma que eligió y el registro de este aviso — y no '
              'utiliza analítica, no muestra publicidad y no carga ningún script de '
              'seguimiento de terceros. Ese tipo de almacenamiento está exento de '
              'consentimiento, por lo que pedírselo sería engañoso.',
        'ro': 'Nu există nimic aici de acceptat sau de refuzat. Acest site stochează '
              'doar ceea ce îi este necesar pentru a funcționa — sesiunea dvs., '
              'tokenul care protejează formularele, limba pe care ați ales-o și '
              'înregistrarea acestei notificări — și nu folosește analitică, nu '
              'afișează publicitate și nu încarcă niciun script de urmărire de la '
              'terți. Acest tip de stocare este scutit de consimțământ, așa că a '
              'vi-l cere ar fi înșelător.',
    },
    'what-you-can-refuse': {
        'en': 'What is strictly necessary cannot be switched off. Everything else is '
              'yours to allow or refuse, now and at any time afterwards.',
        'fr': "Ce qui est strictement nécessaire ne peut pas être désactivé. Tout le "
              "reste, vous pouvez l'autoriser ou le refuser, maintenant et à tout "
              "moment par la suite.",
        'es': 'Lo estrictamente necesario no se puede desactivar. Todo lo demás es '
              'suyo para permitir o rechazar, ahora y en cualquier momento después.',
        'ro': 'Ceea ce este strict necesar nu poate fi dezactivat. Restul vă aparține '
              'să îl permiteți sau să îl refuzați, acum și oricând după aceea.',
    },
    'save-my-choices': {
        'en': 'Save my choices',
        'fr': 'Enregistrer mes choix',
        'es': 'Guardar mis elecciones',
        'ro': 'Salvează alegerile mele',
    },
    'withdraw-my-choice': {
        'en': 'Erase my recorded choice',
        'fr': 'Effacer le choix enregistré',
        'es': 'Borrar mi elección registrada',
        'ro': 'Șterge alegerea înregistrată',
    },
    'choices-saved': {
        'en': 'Your choices have been saved, and anything you refused has been '
              'deleted from this browser.',
        'fr': "Vos choix ont été enregistrés, et ce que vous avez refusé a été "
              "supprimé de ce navigateur.",
        'es': 'Sus elecciones se han guardado y todo lo que rechazó se ha eliminado '
              'de este navegador.',
        'ro': 'Alegerile dvs. au fost salvate, iar ceea ce ați refuzat a fost șters '
              'din acest browser.',
    },
    'choice-cleared': {
        'en': 'Your recorded choice has been erased. The notice will ask again on '
              'your next visit.',
        'fr': "Le choix enregistré a été effacé. L'avis vous sera présenté à nouveau "
              "lors de votre prochaine visite.",
        'es': 'Su elección registrada se ha borrado. El aviso volverá a aparecer en '
              'su próxima visita.',
        'ro': 'Alegerea dvs. înregistrată a fost ștearsă. Notificarea va apărea din '
              'nou la următoarea vizită.',
    },
    'choice-recorded': {
        'en': 'Recorded on this device on {{date}}.',
        'fr': 'Enregistré sur cet appareil le {{date}}.',
        'es': 'Registrado en este dispositivo el {{date}}.',
        'ro': 'Înregistrat pe acest dispozitiv la {{date}}.',
    },
    'choice-not-recorded': {
        'en': 'Nothing is recorded on this device yet.',
        'fr': "Rien n'est encore enregistré sur cet appareil.",
        'es': 'Todavía no hay nada registrado en este dispositivo.',
        'ro': 'Încă nu este înregistrat nimic pe acest dispozitiv.',
    },
    'inventory-unavailable': {
        'en': 'The list could not be loaded. Please try again in a moment — and if '
              'it keeps failing, contact us: you are entitled to this information.',
        'fr': "La liste n'a pas pu être chargée. Réessayez dans un instant — et si "
              "cela persiste, contactez-nous : vous avez droit à cette information.",
        'es': 'No se pudo cargar la lista. Inténtelo de nuevo en un momento y, si '
              'sigue fallando, contáctenos: tiene derecho a esta información.',
        'ro': 'Lista nu a putut fi încărcată. Încercați din nou într-o clipă — iar '
              'dacă persistă, contactați-ne: aveți dreptul la aceste informații.',
    },
    # ── The first-visit notice (CookieNotice.js) ────────────────────────────
    'notice-title': {
        'en': 'Cookies and browser storage',
        'fr': 'Cookies et stockage du navigateur',
        'es': 'Cookies y almacenamiento del navegador',
        'ro': 'Cookie-uri și stocare în browser',
    },
    'notice-information-text': {
        'en': 'This site stores only what it needs to work: your session, the token '
              'that protects forms, the language you chose, and this notice. No '
              'analytics, no advertising, no third-party tracking — so there is '
              'nothing for you to accept or refuse.',
        'fr': "Ce site ne conserve que ce qui lui est nécessaire : votre session, le "
              "jeton qui protège les formulaires, la langue que vous avez choisie et "
              "cet avis. Aucune mesure d'audience, aucune publicité, aucun suivi "
              "tiers — il n'y a donc rien à accepter ni à refuser.",
        'es': 'Este sitio almacena solo lo que necesita para funcionar: su sesión, el '
              'token que protege los formularios, el idioma que eligió y este aviso. '
              'Sin analítica, sin publicidad, sin seguimiento de terceros: no hay '
              'nada que aceptar ni rechazar.',
        'ro': 'Acest site stochează doar ceea ce îi este necesar: sesiunea dvs., '
              'tokenul care protejează formularele, limba pe care ați ales-o și '
              'această notificare. Fără analitică, fără publicitate, fără urmărire '
              'de la terți — deci nu aveți nimic de acceptat sau de refuzat.',
    },
    'notice-consent-text': {
        'en': 'This site stores what it needs to work. It would also like to store '
              'things that are not necessary, and that is your decision — refusing '
              'changes nothing about your access to the site.',
        'fr': "Ce site conserve ce qui lui est nécessaire. Il souhaiterait aussi "
              "conserver des éléments qui ne le sont pas, et cela relève de votre "
              "décision : refuser ne change rien à votre accès au site.",
        'es': 'Este sitio almacena lo que necesita para funcionar. También querría '
              'almacenar cosas que no son necesarias, y eso es su decisión: '
              'rechazarlas no cambia nada en su acceso al sitio.',
        'ro': 'Acest site stochează ceea ce îi este necesar. Ar dori să stocheze și '
              'lucruri care nu sunt necesare, iar aceasta este decizia dvs.: '
              'refuzul nu schimbă nimic în privința accesului dvs. la site.',
    },
    'see-everything-stored': {
        'en': 'See everything this site stores',
        'fr': 'Voir tout ce que ce site conserve',
        'es': 'Ver todo lo que almacena este sitio',
        'ro': 'Vedeți tot ce stochează acest site',
    },
    'understood': {
        'en': 'Understood',
        'fr': "J'ai compris",
        'es': 'Entendido',
        'ro': 'Am înțeles',
    },
    'accept-everything-optional': {
        'en': 'Accept all',
        'fr': 'Tout accepter',
        'es': 'Aceptar todo',
        'ro': 'Acceptă tot',
    },
    'refuse-everything-optional': {
        'en': 'Refuse all',
        'fr': 'Tout refuser',
        'es': 'Rechazar todo',
        'ro': 'Refuză tot',
    },
    'choose-what-to-allow': {
        'en': 'Choose',
        'fr': 'Choisir',
        'es': 'Elegir',
        'ro': 'Alege',
    },
    # ── Categories ──────────────────────────────────────────────────────────
    'category-necessary': {
        'en': 'Strictly necessary',
        'fr': 'Strictement nécessaires',
        'es': 'Estrictamente necesarias',
        'ro': 'Strict necesare',
    },
    'category-necessary-help': {
        'en': 'Needed to deliver the site you asked for: keeping you signed in, '
              'protecting forms against forgery, remembering the language you '
              'picked and remembering this choice. Exempt from consent, and there '
              'is no version of the site that works without them.',
        'fr': "Nécessaires pour fournir le site que vous avez demandé : vous "
              "maintenir connecté, protéger les formulaires contre la falsification, "
              "mémoriser la langue que vous avez choisie et mémoriser ce choix. "
              "Exemptés de consentement, et il n'existe pas de version du site qui "
              "fonctionne sans eux.",
        'es': 'Necesarias para ofrecer el sitio que solicitó: mantener su sesión, '
              'proteger los formularios contra falsificaciones, recordar el idioma '
              'que eligió y recordar esta elección. Exentas de consentimiento, y no '
              'existe una versión del sitio que funcione sin ellas.',
        'ro': 'Necesare pentru a livra site-ul pe care l-ați solicitat: menținerea '
              'autentificării, protejarea formularelor împotriva falsificării, '
              'memorarea limbii alese și memorarea acestei alegeri. Scutite de '
              'consimțământ și nu există o versiune a site-ului care funcționează '
              'fără ele.',
    },
    'category-preferences-help': {
        'en': 'Remembers settings that make the site more comfortable but that it '
              'works perfectly well without.',
        'fr': "Mémorise des réglages qui rendent le site plus confortable, mais dont "
              "il se passe très bien.",
        'es': 'Recuerda ajustes que hacen el sitio más cómodo, pero sin los que '
              'funciona perfectamente.',
        'ro': 'Memorează setări care fac site-ul mai confortabil, dar fără care '
              'funcționează perfect.',
    },
    'category-statistics-help': {
        'en': 'Measures how the site is used, so it can be improved. Nothing here '
              'is needed to serve you a page.',
        'fr': "Mesure l'utilisation du site afin de l'améliorer. Rien ici n'est "
              "nécessaire pour vous servir une page.",
        'es': 'Mide cómo se usa el sitio para poder mejorarlo. Nada de esto es '
              'necesario para servirle una página.',
        'ro': 'Măsoară modul în care este folosit site-ul, pentru a-l putea '
              'îmbunătăți. Nimic de aici nu este necesar pentru a vă servi o pagină.',
    },
    'category-marketing-help': {
        'en': 'Builds a profile of you, usually across other sites, to select '
              'advertising.',
        'fr': "Constitue un profil vous concernant, généralement à travers d'autres "
              "sites, pour sélectionner de la publicité.",
        'es': 'Crea un perfil sobre usted, normalmente a través de otros sitios, '
              'para seleccionar publicidad.',
        'ro': 'Construiește un profil despre dvs., de obicei pe mai multe site-uri, '
              'pentru a selecta publicitate.',
    },
    'category-preferences': {
        'en': 'Preferences',
        'fr': 'Préférences',
        'es': 'Preferencias',
        'ro': 'Preferințe',
    },
    'category-statistics': {
        'en': 'Statistics',
        'fr': 'Statistiques',
        'es': 'Estadísticas',
        'ro': 'Statistici',
    },
    'category-marketing': {
        'en': 'Marketing',
        'fr': 'Marketing',
        'es': 'Marketing',
        'ro': 'Marketing',
    },
    'always-active': {
        'en': 'Always active',
        'fr': 'Toujours actifs',
        'es': 'Siempre activas',
        'ro': 'Întotdeauna active',
    },
    'requires-consent': {
        'en': 'Your choice',
        'fr': 'Votre choix',
        'es': 'Su elección',
        'ro': 'Alegerea dvs.',
    },
    # Singular and plural as two plain keys rather than i18next's `_one`/
    # `_other` suffixes: `seed_translations` stores one text per key per
    # language and knows nothing about plural categories, and Romanian's third
    # category (`few`, which covers 2-19) would fall through to the bare key
    # and render as the key itself. The component picks.
    'entries-stored-one': {
        'en': '{{count}} entry stored',
        'fr': '{{count}} élément conservé',
        'es': '{{count}} elemento almacenado',
        'ro': '{{count}} element stocat',
    },
    'entries-stored': {
        'en': '{{count}} entries stored',
        'fr': '{{count}} éléments conservés',
        'es': '{{count}} elementos almacenados',
        'ro': '{{count}} elemente stocate',
    },
    # ── Table columns ───────────────────────────────────────────────────────
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
    'description': {
        'en': 'Purpose',
        'fr': 'Finalité',
        'es': 'Finalidad',
        'ro': 'Scop',
    },
    'stored-as': {
        'en': 'Stored as',
        'fr': 'Stocké comme',
        'es': 'Almacenado como',
        'ro': 'Stocat ca',
    },
    'stored-as-cookie': {
        'en': 'Cookie',
        'fr': 'Cookie',
        'es': 'Cookie',
        'ro': 'Cookie',
    },
    'stored-as-local_storage': {
        'en': 'Browser storage',
        'fr': 'Stockage du navigateur',
        'es': 'Almacenamiento del navegador',
        'ro': 'Stocare în browser',
    },
    'stored-as-session_storage': {
        'en': 'Session storage',
        'fr': 'Stockage de session',
        'es': 'Almacenamiento de sesión',
        'ro': 'Stocare de sesiune',
    },
    'retention': {
        'en': 'Kept for',
        'fr': 'Durée de conservation',
        'es': 'Conservación',
        'ro': 'Păstrat timp de',
    },
    'retention-session': {
        'en': 'Until you close the browser',
        'fr': "Jusqu'à la fermeture du navigateur",
        'es': 'Hasta que cierre el navegador',
        'ro': 'Până la închiderea browserului',
    },
    'retention-persistent': {
        'en': 'Until you clear it',
        'fr': "Jusqu'à ce que vous l'effaciez",
        'es': 'Hasta que lo borre',
        'ro': 'Până când îl ștergeți',
    },
    'retention-minutes-one': {
        'en': '{{count}} minute',
        'fr': '{{count}} minute',
        'es': '{{count}} minuto',
        'ro': '{{count}} minut',
    },
    'retention-minutes': {
        'en': '{{count}} minutes',
        'fr': '{{count}} minutes',
        'es': '{{count}} minutos',
        'ro': '{{count}} minute',
    },
    'retention-hours-one': {
        'en': '{{count}} hour',
        'fr': '{{count}} heure',
        'es': '{{count}} hora',
        'ro': '{{count}} oră',
    },
    'retention-hours': {
        'en': '{{count}} hours',
        'fr': '{{count}} heures',
        'es': '{{count}} horas',
        'ro': '{{count}} ore',
    },
    'retention-days-one': {
        'en': '{{count}} day',
        'fr': '{{count}} jour',
        'es': '{{count}} día',
        'ro': '{{count}} zi',
    },
    'retention-days': {
        'en': '{{count}} days',
        'fr': '{{count}} jours',
        'es': '{{count}} días',
        'ro': '{{count}} zile',
    },
    'retention-months-one': {
        'en': '{{count}} month',
        'fr': '{{count}} mois',
        'es': '{{count}} mes',
        'ro': '{{count}} lună',
    },
    'retention-months': {
        'en': '{{count}} months',
        'fr': '{{count}} mois',
        'es': '{{count}} meses',
        'ro': '{{count}} luni',
    },
    # ── Third parties ───────────────────────────────────────────────────────
    'third-parties': {
        'en': 'Third parties',
        'fr': 'Tiers',
        'es': 'Terceros',
        'ro': 'Terți',
    },
    'no-third-party-tracking': {
        'en': 'This site loads no advertising, no audience measurement and no social '
              'network script. Every entry in the list above is set by this site '
              'itself, on this domain.',
        'fr': "Ce site ne charge aucune publicité, aucune mesure d'audience et "
              "aucun script de réseau social. Chaque élément de la liste ci-dessus "
              "est déposé par ce site lui-même, sur ce domaine.",
        'es': 'Este sitio no carga publicidad, ni medición de audiencia, ni scripts '
              'de redes sociales. Cada elemento de la lista anterior lo establece '
              'este sitio en este dominio.',
        'ro': 'Acest site nu încarcă publicitate, măsurare a audienței sau scripturi '
              'de rețele sociale. Fiecare element din lista de mai sus este setat de '
              'acest site, pe acest domeniu.',
    },
    # Said plainly because the inventory used to declare two Stripe cookies
    # this site has never set: the payment pages are Stripe's own.
    'payment-on-stripe-pages': {
        'en': 'Payment is handled on Stripe’s own pages: when you pay, you leave '
              'this site, and the cookies Stripe sets are set there, on Stripe’s '
              'domain, under Stripe’s own disclosure. This site loads no Stripe '
              'script and sets no Stripe cookie on this domain.',
        'fr': "Le paiement est traité sur les pages de Stripe : lorsque vous payez, "
              "vous quittez ce site, et les cookies déposés par Stripe le sont "
              "là-bas, sur le domaine de Stripe, sous la propre information de "
              "Stripe. Ce site ne charge aucun script Stripe et ne dépose aucun "
              "cookie Stripe sur ce domaine.",
        'es': 'El pago se gestiona en las propias páginas de Stripe: cuando paga, '
              'sale de este sitio, y las cookies que Stripe establece se establecen '
              'allí, en el dominio de Stripe, bajo la información de Stripe. '
              'Este sitio no carga ningún script de Stripe ni establece ninguna '
              'cookie de Stripe en este dominio.',
        'ro': 'Plata este gestionată pe paginile Stripe: când plătiți, părăsiți acest '
              'site, iar cookie-urile pe care le setează Stripe sunt setate acolo, '
              'pe domeniul Stripe, conform informării Stripe. Acest site nu încarcă '
              'niciun script Stripe și nu setează niciun cookie Stripe pe acest '
              'domeniu.',
    },
    'browser-settings-note': {
        'en': 'Your browser can block or delete all of this at any time, from its '
              'own settings. Blocking the strictly necessary entries will stop you '
              'being able to stay signed in — that is what makes them necessary, '
              'not a penalty for refusing them.',
        'fr': "Votre navigateur peut bloquer ou supprimer tout cela à tout moment, "
              "depuis ses propres réglages. Bloquer les éléments strictement "
              "nécessaires vous empêchera de rester connecté — c'est précisément ce "
              "qui les rend nécessaires, et non une sanction pour les avoir refusés.",
        'es': 'Su navegador puede bloquear o eliminar todo esto en cualquier momento '
              'desde sus propios ajustes. Bloquear los elementos estrictamente '
              'necesarios le impedirá mantener la sesión abierta: eso es lo que los '
              'hace necesarios, no una penalización por rechazarlos.',
        'ro': 'Browserul dvs. poate bloca sau șterge toate acestea oricând, din '
              'propriile setări. Blocarea elementelor strict necesare vă va împiedica '
              'să rămâneți autentificat — exact acest lucru le face necesare, nu o '
              'penalizare pentru refuzul lor.',
    },
    # ── Purposes, one per inventory entry ───────────────────────────────────
    # `Cookie.description` points at the TranslationKey of the same name, so
    # the key IS the storage key. See seed_cookies.py.
    'csrftoken': {
        'en': 'Protects every form you submit against being forged by another site '
              '(cross-site request forgery).',
        'fr': "Protège chaque formulaire que vous envoyez contre une falsification "
              "par un autre site (falsification de requête inter-site).",
        'es': 'Protege cada formulario que envía frente a la falsificación desde '
              'otro sitio (falsificación de solicitudes entre sitios).',
        'ro': 'Protejează fiecare formular pe care îl trimiteți împotriva '
              'falsificării de către un alt site (falsificare de cereri între '
              'site-uri).',
    },
    'sessionid': {
        'en': 'Keeps you signed in between pages. Readable only by the server, '
              'never by a script.',
        'fr': "Vous maintient connecté d'une page à l'autre. Lisible uniquement par "
              "le serveur, jamais par un script.",
        'es': 'Mantiene su sesión abierta entre páginas. Solo lo puede leer el '
              'servidor, nunca un script.',
        'ro': 'Vă menține autentificat între pagini. Poate fi citit doar de server, '
              'niciodată de un script.',
    },
    'user': {
        'en': 'This browser’s copy of who is signed in, so a page can be drawn '
              'correctly before the server has answered.',
        'fr': "La copie, dans ce navigateur, de l'identité connectée, afin qu'une "
              "page puisse s'afficher correctement avant la réponse du serveur.",
        'es': 'La copia en este navegador de quién tiene la sesión abierta, para que '
              'una página pueda dibujarse correctamente antes de que responda el '
              'servidor.',
        'ro': 'Copia din acest browser a cine este autentificat, astfel încât o '
              'pagină să poată fi afișată corect înainte ca serverul să răspundă.',
    },
    'session_expired': {
        'en': 'Records that your session ended on the server, so you are told once '
              'and asked to sign in again rather than shown an error.',
        'fr': "Note que votre session a pris fin sur le serveur, afin que vous en "
              "soyez informé une fois et invité à vous reconnecter plutôt que de "
              "voir une erreur.",
        'es': 'Registra que su sesión terminó en el servidor, para avisarle una vez '
              'y pedirle que vuelva a iniciar sesión en lugar de mostrar un error.',
        'ro': 'Înregistrează faptul că sesiunea dvs. s-a încheiat pe server, astfel '
              'încât să fiți informat o dată și invitat să vă autentificați din nou, '
              'în loc să vedeți o eroare.',
    },
    'i18next': {
        'en': 'The navigation language you selected, so the next page opens in it.',
        'fr': "La langue de navigation que vous avez choisie, afin que la page "
              "suivante s'ouvre dans cette langue.",
        'es': 'El idioma de navegación que seleccionó, para que la página siguiente '
              'se abra en él.',
        'ro': 'Limba de navigare pe care ați selectat-o, astfel încât pagina '
              'următoare să se deschidă în ea.',
    },
    'i18nextLng': {
        'en': 'The navigation language you selected, kept in this browser so it '
              'survives longer than the cookie above.',
        'fr': "La langue de navigation que vous avez choisie, conservée dans ce "
              "navigateur afin qu'elle persiste plus longtemps que le cookie "
              "ci-dessus.",
        'es': 'El idioma de navegación que seleccionó, guardado en este navegador '
              'para que dure más que la cookie anterior.',
        'ro': 'Limba de navigare pe care ați selectat-o, păstrată în acest browser '
              'pentru a dura mai mult decât cookie-ul de mai sus.',
    },
    'mg_consent': {
        'en': 'Your answer to the storage notice, and when you gave it — so you are '
              'not asked again, and so a refusal can be honoured.',
        'fr': "Votre réponse à l'avis sur le stockage et la date à laquelle vous "
              "l'avez donnée — afin de ne pas vous la redemander et de pouvoir "
              "respecter un refus.",
        'es': 'Su respuesta al aviso sobre almacenamiento y cuándo la dio, para no '
              'volver a preguntarle y poder respetar un rechazo.',
        'ro': 'Răspunsul dvs. la notificarea privind stocarea și momentul în care '
              'l-ați dat — pentru a nu vă întreba din nou și pentru a putea respecta '
              'un refuz.',
    },
    'page-has-been-force-refreshed': {
        'en': 'Notes that the page was reloaded once after a failed update, so a '
              'broken deployment cannot put this browser into a reload loop.',
        'fr': "Note que la page a été rechargée une fois après une mise à jour "
              "échouée, afin qu'un déploiement défectueux ne puisse pas enfermer ce "
              "navigateur dans une boucle de rechargement.",
        'es': 'Anota que la página se recargó una vez tras una actualización '
              'fallida, para que un despliegue defectuoso no pueda meter este '
              'navegador en un bucle de recarga.',
        'ro': 'Notează că pagina a fost reîncărcată o dată după o actualizare '
              'eșuată, astfel încât o implementare defectă să nu poată bloca acest '
              'browser într-o buclă de reîncărcare.',
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
    'tfa-email-subject': {
        'en': 'Your security code',
        'fr': 'Votre code de sécurité',
        'es': 'Tu código de seguridad',
        'ro': 'Codul tău de securitate',
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
    'agent-install-title': {
        'en': 'Installing from an AI agent',
        'fr': 'Installation depuis un agent IA',
        'es': 'Instalación desde un agente IA',
        'ro': 'Instalare dintr-un agent IA',
    },
    'agent-install-desc': {
        'en': 'This wizard is for a human operator. An autonomous AI agent does not need to log in here: if it generated an application with its own Migratis access token it already holds the package, so it can install it directly by POSTing the package to the installer\'s install-package endpoint — no second login, and in-place upgrades use upgrade-package the same way.',
        'fr': 'Cet assistant est destiné à un opérateur humain. Un agent IA autonome n\'a pas besoin de se connecter ici : s\'il a généré une application avec son propre jeton d\'accès Migratis, il détient déjà le paquet et peut donc l\'installer directement en envoyant (POST) le paquet au point d\'accès install-package de l\'installateur — sans seconde connexion, et les mises à niveau sur place utilisent upgrade-package de la même manière.',
        'es': 'Este asistente es para un operador humano. Un agente IA autónomo no necesita iniciar sesión aquí: si generó una aplicación con su propio token de acceso de Migratis, ya posee el paquete, por lo que puede instalarlo directamente enviando (POST) el paquete al endpoint install-package del instalador, sin un segundo inicio de sesión, y las actualizaciones in situ usan upgrade-package del mismo modo.',
        'ro': 'Acest asistent este pentru un operator uman. Un agent IA autonom nu trebuie să se autentifice aici: dacă a generat o aplicație cu propriul token de acces Migratis, deține deja pachetul, așa că îl poate instala direct trimițând (POST) pachetul către endpointul install-package al instalatorului — fără a doua autentificare, iar actualizările pe loc folosesc upgrade-package în același mod.',
    },
    'agent-install-security': {
        'en': 'Because these endpoints apply code into the running project, they are loopback-only by default; to allow a remote agent, set INSTALLER_AGENT_TOKEN in the backend environment and have the agent send it as an X-Installer-Token header. Disable the installer (INSTALLER=False) once installation is finished.',
        'fr': 'Comme ces points d\'accès appliquent du code dans le projet en cours d\'exécution, ils sont par défaut limités au bouclage local ; pour autoriser un agent distant, définissez INSTALLER_AGENT_TOKEN dans l\'environnement du backend et faites envoyer ce jeton par l\'agent dans un en-tête X-Installer-Token. Désactivez l\'installateur (INSTALLER=False) une fois l\'installation terminée.',
        'es': 'Como estos endpoints aplican código en el proyecto en ejecución, por defecto solo son accesibles desde localhost; para permitir un agente remoto, defina INSTALLER_AGENT_TOKEN en el entorno del backend y haga que el agente lo envíe como una cabecera X-Installer-Token. Desactive el instalador (INSTALLER=False) una vez finalizada la instalación.',
        'ro': 'Deoarece aceste endpointuri aplică cod în proiectul care rulează, sunt implicit accesibile doar prin loopback; pentru a permite un agent la distanță, setați INSTALLER_AGENT_TOKEN în mediul backendului și faceți ca agentul să îl trimită ca antet X-Installer-Token. Dezactivați instalatorul (INSTALLER=False) după finalizarea instalării.',
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
    'recompiling-frontend': {
        'en': 'Finishing up — rebuilding the frontend…',
        'fr': 'Finalisation — reconstruction du frontend…',
        'es': 'Finalizando — reconstruyendo el frontend…',
        'ro': 'Se finalizează — se reconstruiește frontendul…',
    },
    'recompiling-frontend-help': {
        'en': 'Please wait for the rebuild to complete before continuing.',
        'fr': 'Veuillez attendre la fin de la reconstruction avant de continuer.',
        'es': 'Espere a que termine la reconstrucción antes de continuar.',
        'ro': 'Așteptați finalizarea reconstrucției înainte de a continua.',
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
    'uninstall-would-orphan-data': {
        'en': 'Nothing was removed: reverting the migrations failed and the module '
              'still holds data.',
        'fr': "Rien n'a été supprimé : l'annulation des migrations a échoué et le "
              "module contient encore des données.",
        'es': 'No se eliminó nada: revertir las migraciones falló y el módulo todavía '
              'contiene datos.',
        'ro': 'Nu s-a șters nimic: revenirea migrărilor a eșuat, iar modulul încă '
              'conține date.',
    },
    'uninstall-orphan-explanation': {
        'en': 'Deleting the files now would leave these behind with nothing on disk '
              'that mentions them, and the next install would fail because the tables '
              'already exist. Repair the migration graph and retry, or force the '
              'removal — which saves a backup under backups/ first, then drops them.',
        'fr': "Supprimer les fichiers maintenant les laisserait en place sans que rien "
              "sur le disque n'y fasse référence, et la prochaine installation "
              "échouerait car les tables existent déjà. Réparez le graphe de migrations "
              "puis réessayez, ou forcez la suppression — une sauvegarde est alors "
              "enregistrée dans backups/ avant l'effacement.",
        'es': 'Eliminar los archivos ahora los dejaría sin nada en el disco que los '
              'mencione, y la próxima instalación fallaría porque las tablas ya '
              'existen. Repare el grafo de migraciones y vuelva a intentarlo, o fuerce '
              'la eliminación: primero se guarda una copia en backups/ y luego se '
              'eliminan.',
        'ro': 'Ștergerea fișierelor acum le-ar lăsa în urmă fără nimic pe disc care să '
              'le menționeze, iar următoarea instalare ar eșua pentru că tabelele '
              'există deja. Reparați graful de migrări și reîncercați, sau forțați '
              'ștergerea — se salvează mai întâi o copie în backups/, apoi se șterg.',
    },
    'uninstall-orphan-tables': {
        'en': 'Tables still present', 'fr': 'Tables encore présentes',
        'es': 'Tablas aún presentes', 'ro': 'Tabele încă prezente',
    },
    'uninstall-orphan-migrations': {
        'en': 'Migrations still recorded', 'fr': 'Migrations encore enregistrées',
        'es': 'Migraciones aún registradas', 'ro': 'Migrări încă înregistrate',
    },
    'force-uninstall': {
        'en': 'Back up and force removal', 'fr': 'Sauvegarder et forcer la suppression',
        'es': 'Copiar y forzar la eliminación', 'ro': 'Salvează și forțează ștergerea',
    },
    'confirm-force-uninstall': {
        'en': 'This deletes the data of "{{module}}" permanently. A backup is written '
              'to backups/ first. Continue?',
        'fr': "Ceci supprime définitivement les données de « {{module}} ». Une "
              "sauvegarde est d'abord écrite dans backups/. Continuer ?",
        'es': 'Esto elimina permanentemente los datos de «{{module}}». Primero se '
              'escribe una copia en backups/. ¿Continuar?',
        'ro': 'Aceasta șterge definitiv datele modulului „{{module}}". Mai întâi se '
              'scrie o copie în backups/. Continuați?',
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
    'config-stripe': {
        'en': 'Stripe keys', 'fr': 'Clés Stripe',
        'es': 'Claves de Stripe', 'ro': 'Chei Stripe',
    },
    # One field per external source the application declares. The variable name
    # is the label, because that is what goes in the .env file.
    'config-datasource': {
        'en': 'External source keys', 'fr': 'Clés des sources externes',
        'es': 'Claves de fuentes externas', 'ro': 'Chei pentru surse externe',
    },
    'config-datasource-help': {
        'en': 'This application reads from an external API. Migratis never '
              'receives or ships a key — it belongs to this deployment. Leave a '
              'field blank to set it later; the install will say which are '
              'still missing.',
        'fr': "Cette application interroge une API externe. Migratis ne reçoit "
              "ni ne livre jamais de clé — elle appartient à ce déploiement. "
              "Laissez un champ vide pour le renseigner plus tard ; "
              "l'installation indiquera lesquelles manquent encore.",
        'es': 'Esta aplicación consulta una API externa. Migratis nunca recibe '
              'ni entrega una clave — pertenece a esta instalación. Deje un '
              'campo en blanco para definirlo más tarde; la instalación '
              'indicará cuáles siguen faltando.',
        'ro': 'Această aplicație interoghează un API extern. Migratis nu '
              'primește și nu livrează niciodată o cheie — ea aparține acestei '
              'instalări. Lăsați un câmp gol pentru a-l completa mai târziu; '
              'instalarea va indica ce chei lipsesc.',
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
    'upgrade-badge': {
        'en': 'update v{{from}} → v{{to}}', 'fr': 'mise à jour v{{from}} → v{{to}}',
        'es': 'actualización v{{from}} → v{{to}}', 'ro': 'actualizare v{{from}} → v{{to}}',
    },
    'upgrade-selected': {
        'en': 'Upgrade selected', 'fr': 'Mettre à jour la sélection',
        'es': 'Actualizar la selección', 'ro': 'Actualizează selecția',
    },
    'upgrade-title': {
        'en': 'Upgrade {{app}}', 'fr': 'Mettre à jour {{app}}',
        'es': 'Actualizar {{app}}', 'ro': 'Actualizează {{app}}',
    },
    'upgrade-versions': {
        'en': 'From version {{from}} to version {{to}}. Your data is kept; the schema changes below will be applied.',
        'fr': 'De la version {{from}} à la version {{to}}. Vos données sont conservées ; les changements de schéma ci-dessous seront appliqués.',
        'es': 'De la versión {{from}} a la versión {{to}}. Sus datos se conservan; se aplicarán los cambios de esquema siguientes.',
        'ro': 'De la versiunea {{from}} la versiunea {{to}}. Datele sunt păstrate; modificările de schemă de mai jos vor fi aplicate.',
    },
    'upgrade-legacy-warning': {
        'en': 'This application was installed before upgrade support. The upgrade keeps your data only if the schema was not changed before the first versioned generation.',
        'fr': "Cette application a été installée avant la prise en charge des mises à jour. La mise à jour conserve vos données uniquement si le schéma n'a pas été modifié avant la première génération versionnée.",
        'es': 'Esta aplicación se instaló antes de la compatibilidad con actualizaciones. La actualización conserva sus datos solo si el esquema no se modificó antes de la primera generación versionada.',
        'ro': 'Această aplicație a fost instalată înainte de suportul pentru actualizări. Actualizarea păstrează datele doar dacă schema nu a fost modificată înainte de prima generare versionată.',
    },
    'upgrade-no-schema-changes': {
        'en': 'No schema changes — only the application code will be updated.',
        'fr': "Aucun changement de schéma — seul le code de l'application sera mis à jour.",
        'es': 'Sin cambios de esquema: solo se actualizará el código de la aplicación.',
        'ro': 'Fără modificări de schemă — doar codul aplicației va fi actualizat.',
    },
    'upgrade-op-add_field': {
        'en': 'new field', 'fr': 'nouveau champ', 'es': 'campo nuevo', 'ro': 'câmp nou',
    },
    'upgrade-op-remove_field': {
        'en': 'field removed (data dropped)', 'fr': 'champ supprimé (données perdues)',
        'es': 'campo eliminado (datos perdidos)', 'ro': 'câmp eliminat (date pierdute)',
    },
    'upgrade-op-rename_field': {
        'en': 'field renamed', 'fr': 'champ renommé', 'es': 'campo renombrado', 'ro': 'câmp redenumit',
    },
    'upgrade-op-alter_field': {
        'en': 'type changed', 'fr': 'type modifié', 'es': 'tipo modificado', 'ro': 'tip modificat',
    },
    'upgrade-op-create_model': {
        'en': 'new entity', 'fr': 'nouvelle entité', 'es': 'entidad nueva', 'ro': 'entitate nouă',
    },
    'upgrade-op-delete_model': {
        'en': 'entity removed (all its data dropped)', 'fr': 'entité supprimée (toutes ses données perdues)',
        'es': 'entidad eliminada (todos sus datos perdidos)', 'ro': 'entitate eliminată (toate datele pierdute)',
    },
    'upgrade-op-rename_model': {
        'en': 'entity renamed', 'fr': 'entité renommée', 'es': 'entidad renombrada', 'ro': 'entitate redenumită',
    },
    'upgrade-rows-affected': {
        'en': '{{count}} rows affected', 'fr': '{{count}} lignes concernées',
        'es': '{{count}} filas afectadas', 'ro': '{{count}} rânduri afectate',
    },
    'upgrade-destructive-warning': {
        'en': 'Some changes above are destructive: the highlighted data will be permanently lost. A backup is taken first, but confirm only if you accept these losses.',
        'fr': 'Certains changements ci-dessus sont destructifs : les données en surbrillance seront définitivement perdues. Une sauvegarde est effectuée au préalable, mais ne confirmez que si vous acceptez ces pertes.',
        'es': 'Algunos cambios anteriores son destructivos: los datos resaltados se perderán de forma permanente. Primero se hace una copia de seguridad, pero confirme solo si acepta estas pérdidas.',
        'ro': 'Unele modificări de mai sus sunt distructive: datele evidențiate vor fi pierdute definitiv. Se face mai întâi o copie de rezervă, dar confirmați doar dacă acceptați aceste pierderi.',
    },
    'upgrade-backup-notice': {
        'en': 'A full data dump and a code snapshot are stored in backups/ before anything is changed; if the migration fails, the previous version is restored automatically.',
        'fr': "Une sauvegarde complète des données et un instantané du code sont stockés dans backups/ avant toute modification ; si la migration échoue, la version précédente est restaurée automatiquement.",
        'es': 'Antes de cualquier cambio se guarda un volcado completo de datos y una instantánea del código en backups/; si la migración falla, la versión anterior se restaura automáticamente.',
        'ro': 'Înainte de orice modificare, o copie completă a datelor și un instantaneu al codului sunt stocate în backups/; dacă migrarea eșuează, versiunea anterioară este restaurată automat.',
    },
    'upgrade-confirm': {
        'en': 'Confirm upgrade', 'fr': 'Confirmer la mise à jour',
        'es': 'Confirmar la actualización', 'ro': 'Confirmă actualizarea',
    },
    'upgrade-success': {
        'en': '{{module}} upgraded from v{{from}} to v{{to}}. Your data was kept.',
        'fr': '{{module}} mis à jour de v{{from}} à v{{to}}. Vos données ont été conservées.',
        'es': '{{module}} actualizado de v{{from}} a v{{to}}. Sus datos se conservaron.',
        'ro': '{{module}} actualizat de la v{{from}} la v{{to}}. Datele au fost păstrate.',
    },
    'upgrade-failed-msg': {
        'en': 'The upgrade migration failed.', 'fr': 'La migration de mise à jour a échoué.',
        'es': 'La migración de actualización falló.', 'ro': 'Migrarea de actualizare a eșuat.',
    },
    'upgrade-rolled-back': {
        'en': 'The previous version was restored automatically; your data is intact.',
        'fr': 'La version précédente a été restaurée automatiquement ; vos données sont intactes.',
        'es': 'La versión anterior se restauró automáticamente; sus datos están intactos.',
        'ro': 'Versiunea anterioară a fost restaurată automat; datele sunt intacte.',
    },
    'upgrade-rollback-failed': {
        'en': 'Automatic rollback could not complete — restore manually from the backup below.',
        'fr': "La restauration automatique n'a pas pu aboutir — restaurez manuellement à partir de la sauvegarde ci-dessous.",
        'es': 'La reversión automática no pudo completarse: restaure manualmente desde la copia de seguridad siguiente.',
        'ro': 'Revenirea automată nu a putut fi finalizată — restaurați manual din copia de rezervă de mai jos.',
    },
    'upgrade-backup-at': {
        'en': 'Backup stored at', 'fr': 'Sauvegarde stockée dans',
        'es': 'Copia de seguridad guardada en', 'ro': 'Copie de rezervă stocată în',
    },
    'upgrade-translations-hint': {
        'en': 'Your data was not touched. The translation keys this version adds are '
              'loaded on the restart above; if a word still shows as its key, run:',
        'fr': "Vos données n'ont pas été modifiées. Les clés de traduction ajoutées par "
              "cette version sont chargées au redémarrage ci-dessus ; si un mot "
              "s'affiche encore sous forme de clé, exécutez :",
        'es': 'Sus datos no se modificaron. Las claves de traducción que añade esta '
              'versión se cargan en el reinicio indicado arriba; si una palabra sigue '
              'apareciendo como su clave, ejecute:',
        'ro': 'Datele dvs. nu au fost modificate. Cheile de traducere adăugate de '
              'această versiune se încarcă la repornirea de mai sus; dacă un cuvânt '
              'apare încă sub formă de cheie, rulați:',
    },
    'upgrade-failed': {
        'en': 'Upgrade failed', 'fr': 'Échec de la mise à jour',
        'es': 'Error en la actualización', 'ro': 'Actualizarea a eșuat',
    },
    'upgrade-drift-repaired': {
        'en': '{{count}} missing column(s) from a pre-versioning install were added automatically (additive repair, no data touched):',
        'fr': "{{count}} colonne(s) manquante(s) d'une installation antérieure au versionnage ont été ajoutées automatiquement (réparation additive, aucune donnée modifiée) :",
        'es': 'Se añadieron automáticamente {{count}} columna(s) que faltaban de una instalación previa al versionado (reparación aditiva, sin tocar los datos):',
        'ro': '{{count}} coloană/coloane lipsă dintr-o instalare anterioară versionării au fost adăugate automat (reparație aditivă, fără a atinge datele):',
    },
}

# ===========================================================================
# generator
# ===========================================================================


# ===========================================================================
# entity
# (shared keys are linked via NAMESPACE_LINKS, not duplicated here)
# ===========================================================================


# ===========================================================================
# field
# (shared keys are linked via NAMESPACE_LINKS, not duplicated here)
# ===========================================================================


TRANSLATIONS['home'] = {
    'hero-title': {
        'en': 'Build Apps with AI',
        'fr': 'Construire des Apps avec l\'IA',
        'es': 'Crear Apps con IA',
        'ro': 'Construiește Aplicații cu AI',
    },
    'hero-subtitle': {
        'en': 'Design, prototype, and generate full-stack applications powered by AI',
        'fr': 'Concevez, prototypisez et générez des applications full-stack alimentées par l\'IA',
        'es': 'Diseña, prototipa y genera aplicaciones full-stack impulsadas por IA',
        'ro': 'Proiectează, prototipează și generează aplicații full-stack alimentate de AI',
    },
    'get-started': {
        'en': 'Get Started',
        'fr': 'Commencer',
        'es': 'Empezar',
        'ro': 'Începe',
    },
    'ch1-title': {
        'en': 'AI-Powered Schema Design',
        'fr': 'Conception de schéma alimentée par l\'IA',
        'es': 'Diseño de esquema con IA',
        'ro': 'Proiectare schemă cu AI',
    },
    'ch1-desc': {
        'en': 'Describe your application in plain language and let the AI generate the complete data model with entities, fields, relationships, roles, and validation rules.',
        'fr': "Décrivez votre application en langage naturel et laissez l'IA générer le modèle de données complet avec entités, champs, relations, rôles et règles de validation.",
        'es': 'Describe tu aplicación en lenguaje natural y deja que la IA genere el modelo de datos completo con entidades, campos, relaciones, roles y reglas de validación.',
        'ro': 'Descrie aplicația ta în limbaj natural și lasă AI-ul să genereze modelul de date complet cu entități, câmpuri, relații, roluri și reguli de validare.',
    },
    'ch1-f1': {
        'en': 'Natural language application descriptions',
        'fr': 'Descriptions d\'application en langage naturel',
        'es': 'Descripciones de aplicación en lenguaje natural',
        'ro': 'Descrieri de aplicații în limbaj natural',
    },
    'ch1-f2': {
        'en': 'Automatic entity and field generation',
        'fr': 'Génération automatique d\'entités et de champs',
        'es': 'Generación automática de entidades y campos',
        'ro': 'Generare automată de entități și câmpuri',
    },
    'ch1-f3': {
        'en': 'Smart relationship detection',
        'fr': 'Détection intelligente des relations',
        'es': 'Detección inteligente de relaciones',
        'ro': 'Detecție inteligentă a relațiilor',
    },
    'ch1-f4': {
        'en': 'Review every AI change before it is applied',
        'fr': "Vérifiez chaque modification de l'IA avant application",
        'es': 'Revisa cada cambio de la IA antes de aplicarlo',
        'ro': 'Verifică fiecare modificare AI înainte de aplicare',
    },
    'ch2-title': {
        'en': 'Interactive Sandbox Testing',
        'fr': 'Tests interactifs dans un bac à sable',
        'es': 'Pruebas interactivas en sandbox',
        'ro': 'Testare interactivă în sandbox',
    },
    'ch2-desc': {
        'en': 'Test your data model in a live sandbox environment before generating any code. Create, edit, and delete records to verify your schema works exactly as intended.',
        'fr': 'Testez votre modèle de données dans un environnement bac à sable vivant avant de générer du code. Créez, modifiez et supprimez des enregistrements pour vérifier que votre schéma fonctionne comme prévu.',
        'es': 'Prueba tu modelo de datos en un entorno sandbox vivo antes de generar código. Crea, edita y elimina registros para verificar que tu esquema funciona exactamente como se desea.',
        'ro': 'Testează modelul de date într-un mediu sandbox live înainte de a genera cod. Creează, editează și șterge înregistrări pentru a verifica că schema funcționează exact cum dorești.',
    },
    'ch2-f1': {
        'en': 'Real-time data model testing',
        'fr': 'Test du modèle de données en temps réel',
        'es': 'Prueba del modelo de datos en tiempo real',
        'ro': 'Testare model de date în timp real',
    },
    'ch2-f2': {
        'en': 'Search, filter, and sort records',
        'fr': 'Rechercher, filtrer et trier les enregistrements',
        'es': 'Buscar, filtrar y ordenar registros',
        'ro': 'Căutare, filtrare și sortare înregistrări',
    },
    'ch2-f3': {
        'en': 'Multiple display modes (table, cards, kanban, gallery, map)',
        'fr': "Modes d'affichage multiples (tableau, cartes, kanban, galerie, carte géographique)",
        'es': 'Múltiples modos de visualización (tabla, tarjetas, kanban, galería, mapa)',
        'ro': 'Moduri de afișare multiple (tabel, carduri, kanban, galerie, hartă)',
    },
    'ch2-f4': {
        'en': 'Preview the app as any role or member',
        'fr': "Prévisualisez l'application avec n'importe quel rôle ou membre",
        'es': 'Previsualiza la aplicación con cualquier rol o miembro',
        'ro': 'Previzualizează aplicația ca orice rol sau membru',
    },
    'ch3-title': {
        'en': 'One-Click Code Generation',
        'fr': 'Génération de code en un clic',
        'es': 'Generación de código con un clic',
        'ro': 'Generare cod cu un clic',
    },
    'ch3-desc': {
        'en': 'Generate production-ready Django backend and React frontend code from your validated schema. Everything you need to deploy your application.',
        'fr': 'Générez du code Django backend et React frontend prêt pour la production à partir de votre schéma validé. Tout ce dont vous avez besoin pour déployer votre application.',
        'es': 'Genera código Django backend y React frontend listo para producción a partir de tu esquema validado. Todo lo que necesitas para implementar tu aplicación.',
        'ro': 'Generează cod Django backend și React frontend ready pentru producție din schema ta validată. Tot ce ai nevoie pentru a implementa aplicația.',
    },
    'ch3-f1': {
        'en': 'Django models and APIs',
        'fr': 'Modèles et API Django',
        'es': 'Modelos y APIs de Django',
        'ro': 'Modele și API-uri Django',
    },
    'ch3-f2': {
        'en': 'React components and forms',
        'fr': 'Composants et formulaires React',
        'es': 'Componentes y formularios de React',
        'ro': 'Componente și formulare React',
    },
    'ch3-f3': {
        'en': 'Admin interface configuration',
        'fr': 'Configuration de l\'interface d\'administration',
        'es': 'Configuración de la interfaz de administración',
        'ro': 'Configurare interfață de administrare',
    },
    'ch3-f4': {
        'en': 'Database migrations included',
        'fr': 'Migrations de base de données incluses',
        'es': 'Migraciones de base de datos incluidas',
        'ro': 'Migrații de bază de date incluse',
    },
    'ch4-title': {
        'en': 'Public "base" Repository',
        'fr': 'Dépôt public "base"',
        'es': 'Repositorio público "base"',
        'ro': 'Depozit public "base"',
    },
    'ch4-desc': {
        'en': 'Migratis provides a public GitHub repository called "base" from which you can install any application generated by the platform. Your apps are ready to deploy in minutes.',
        'fr': 'Migratis fournit un dépôt GitHub public appelé "base" à partir duquel vous pouvez installer n\'importe quelle application générée par la plateforme. Vos applications sont prêtes à être déployées en quelques minutes.',
        'es': 'Migratis proporciona un repositorio público de GitHub llamado "base" desde el cual puedes instalar cualquier aplicación generada por la plataforma. Tus aplicaciones están listas para implementar en minutos.',
        'ro': 'Migratis oferă un depozit GitHub public numit "base" de pe care poți instala orice aplicație generată de platformă. Aplicațiile tale sunt gata de implementat în minute.',
    },
    'ch4-f1': {
        'en': 'Pre-configured Django project structure',
        'fr': 'Structure de projet Django pré-configurée',
        'es': 'Estructura de proyecto Django preconfigurada',
        'ro': 'Structură de proiect Django preconfigurată',
    },
    'ch4-f2': {
        'en': 'Ready-to-install application modules',
        'fr': 'Modules d\'application prêts à installer',
        'es': 'Módulos de aplicación listos para instalar',
        'ro': 'Module de aplicație ready-to-install',
    },
    'ch4-f3': {
        'en': 'One-command deployment setup',
        'fr': 'Configuration de déploiement en une commande',
        'es': 'Configuración de implementación con un comando',
        'ro': 'Configurare deployment cu o singură comandă',
    },
    'ch4-f4': {
        'en': 'Re-generate and upgrade an installed app',
        'fr': 'Régénérez et mettez à niveau une application installée',
        'es': 'Regenera y actualiza una aplicación instalada',
        'ro': 'Regenerează și actualizează o aplicație instalată',
    },
    'ch5-title': {
        'en': 'Multi-Language Support',
        'fr': 'Support multi-langue',
        'es': 'Soporte multilingüe',
        'ro': 'Suport multilingv',
    },
    'ch5-desc': {
        'en': 'Build applications that support multiple languages out of the box. Our AI generates translations for all your entities and fields.',
        'fr': 'Construisez des applications qui supportent plusieurs langues dès le départ. Notre IA génère des traductions pour toutes vos entités et champs.',
        'es': 'Construye aplicaciones que soportan múltiples idiomas desde el principio. Nuestra IA genera traducciones para todas tus entidades y campos.',
        'ro': 'Construiește aplicații care suportă multiple limbi din start. AI-ul nostru generează traduceri pentru toate entitățile și câmpurile tale.',
    },
    'ch5-f1': {
        'en': 'Built-in i18n support',
        'fr': 'Support i18n intégré',
        'es': 'Soporte i18n incorporado',
        'ro': 'Suport i18n integrat',
    },
    'ch5-f2': {
        'en': 'AI-generated translations',
        'fr': 'Traductions générées par l\'IA',
        'es': 'Traducciones generadas por IA',
        'ro': 'Traduceri generate de AI',
    },
    'ch5-f3': {
        'en': '40+ languages supported',
        'fr': 'Plus de 40 langues supportées',
        'es': 'Más de 40 idiomas soportados',
        'ro': 'Peste 40 de limbi suportate',
    },
    'ch5-f4': {
        'en': 'Easy translation management',
        'fr': 'Gestion facile des traductions',
        'es': 'Gestión fácil de traducciones',
        'ro': 'Management ușor al traducerilor',
    },
    'ch6-title': {
        'en': 'Ready-Made Modules',
        'fr': 'Modules prêts à l\'emploi',
        'es': 'Módulos listos para usar',
        'ro': 'Module gata de utilizare',
    },
    'ch6-desc': {
        'en': 'Accelerate development with pre-built modules for authentication, payments, internationalization, support tickets, and cookie consent.',
        'fr': "Accélérez le développement avec des modules pré-construits pour l'authentification, les paiements, l'internationalisation, les tickets de support et le consentement aux cookies.",
        'es': 'Acelera el desarrollo con módulos preconstruidos para autenticación, pagos, internacionalización, tickets de soporte y consentimiento de cookies.',
        'ro': 'Accelerează dezvoltarea cu module pre-construite pentru autentificare, plăți, internaționalizare, tichete de suport și consimțământ cookie.',
    },
    'ch6-f1': {
        'en': 'User authentication & profiles',
        'fr': 'Authentification et profils utilisateur',
        'es': 'Autenticación y perfiles de usuario',
        'ro': 'Autentificare și profiluri utilizator',
    },
    'ch6-f2': {
        'en': 'Stripe subscriptions or metered credits',
        'fr': 'Abonnements Stripe ou crédits à l’usage',
        'es': 'Suscripciones Stripe o créditos por uso',
        'ro': 'Abonamente Stripe sau credite pe consum',
    },
    'ch6-f3': {
        'en': 'GDPR cookie consent',
        'fr': 'Consentement aux cookies RGPD',
        'es': 'Consentimiento de cookies RGPD',
        'ro': 'Consimțământ cookie GDPR',
    },
    'ch6-f4': {
        'en': 'Customer support system',
        'fr': 'Système de support client',
        'es': 'Sistema de soporte al cliente',
        'ro': 'Sistem de suport clienți',
    },
    'ch7-title': {
        'en': 'Security & Best Practices',
        'fr': 'Sécurité et bonnes pratiques',
        'es': 'Seguridad y mejores prácticas',
        'ro': 'Securitate și bune practici',
    },
    'ch7-desc': {
        'en': 'Your application follows security best practices with built-in protection against common vulnerabilities, role-based access control, and regular security updates.',
        'fr': 'Votre application suit les bonnes pratiques de sécurité avec une protection intégrée contre les vulnérabilités courantes, un contrôle d\'accès basé sur les rôles et des mises à jour de sécurité régulières.',
        'es': 'Tu aplicación sigue las mejores prácticas de seguridad con protección integrada contra vulnerabilidades comunes, control de acceso basado en roles y actualizaciones de seguridad regulares.',
        'ro': 'Aplicația ta respectă cele mai bune practici de securitate cu protecție integrată împotriva vulnerabilităților comune, control de acces bazat pe roluri și actualizări de securitate regulate.',
    },
    'ch7-f1': {
        'en': 'SQL injection prevention',
        'fr': 'Prévention des injections SQL',
        'es': 'Prevención de inyección SQL',
        'ro': 'Prevenire injectare SQL',
    },
    'ch7-f2': {
        'en': 'CSRF protection included',
        'fr': 'Protection CSRF incluse',
        'es': 'Protección CSRF incluida',
        'ro': 'Protecție CSRF inclusă',
    },
    'ch7-f3': {
        'en': 'Role-based access control',
        'fr': 'Contrôle d\'accès basé sur les rôles',
        'es': 'Control de acceso basado en roles',
        'ro': 'Control acces bazat pe roluri',
    },
    'ch7-f4': {
        'en': 'Secure password hashing',
        'fr': 'Hachage de mot de passe sécurisé',
        'es': 'Hash de contraseña seguro',
        'ro': 'Hash parolă sigur',
    },
    'ch8-title': {
        'en': 'Workflow Automation',
        'fr': 'Automatisation des flux de travail',
        'es': 'Automatización de flujos de trabajo',
        'ro': 'Automatizare fluxuri de lucru',
    },
    'ch8-desc': {
        'en': 'Define automated workflows that trigger actions based on events. Create, update, compute, and export data automatically with AI-guided logic.',
        'fr': 'Définissez des flux de travail automatisés qui déclenchent des actions basées sur des événements. Créez, mettez à jour, calculez et exportez des données automatiquement avec une logique guidée par l\'IA.',
        'es': 'Define flujos de trabajo automatizados que déclenchan acciones basadas en eventos. Crea, actualiza, calcula y exporta datos automáticamente con lógica guiada por IA.',
        'ro': 'Definește fluxuri de lucru automatizate care declanșează acțiuni bazate pe evenimente. Creează, actualizează, calculează și exportă date automat cu logică ghidată de AI.',
    },
    'ch8-f1': {
        'en': 'Event-driven automation',
        'fr': 'Automatisation basée sur les événements',
        'es': 'Automatización basada en eventos',
        'ro': 'Automatizare bazată pe evenimente',
    },
    'ch8-f2': {
        'en': 'AI-assisted workflow design',
        'fr': 'Conception de flux de travail assistée par l\'IA',
        'es': 'Diseño de flujo de trabajo asistido por IA',
        'ro': 'Proiectare flux de lucru asistată de AI',
    },
    'ch8-f3': {
        'en': 'Branching steps with preconditions',
        'fr': 'Étapes conditionnelles avec préconditions',
        'es': 'Pasos con ramificaciones y precondiciones',
        'ro': 'Pași cu ramificații și precondiții',
    },
    'ch8-f4': {
        'en': 'Per-step role gating',
        'fr': 'Contrôle des rôles à chaque étape',
        'es': 'Control de rol en cada paso',
        'ro': 'Control de rol la fiecare pas',
    },
    # ch9 / ch10 / ch11 — model choice, the per-application role ladder and
    # location fields. Chapter order lives in frontend Home.js, not here.
    'ch9-title': {
        'en': 'Choose Your AI Model',
        'fr': 'Choisissez votre modèle d\'IA',
        'es': 'Elige tu modelo de IA',
        'ro': 'Alege modelul tău AI',
    },
    'ch9-desc': {
        'en': 'Pick the model behind every AI call. OpenAI, Anthropic, Gemini, xAI, and DeepSeek are all available, each priced per call so you stay in control of the cost.',
        'fr': 'Choisissez le modèle derrière chaque appel à l\'IA. OpenAI, Anthropic, Gemini, xAI et DeepSeek sont disponibles, chacun facturé à l\'appel pour garder le contrôle des coûts.',
        'es': 'Elige el modelo detrás de cada llamada a la IA. OpenAI, Anthropic, Gemini, xAI y DeepSeek están disponibles, cada uno tarificado por llamada para que controles el coste.',
        'ro': 'Alege modelul din spatele fiecărui apel AI. OpenAI, Anthropic, Gemini, xAI și DeepSeek sunt disponibile, fiecare tarifat per apel ca să controlezi costul.',
    },
    'ch9-f1': {
        'en': 'Five providers, one picker',
        'fr': 'Cinq fournisseurs, un seul sélecteur',
        'es': 'Cinco proveedores, un solo selector',
        'ro': 'Cinci furnizori, un singur selector',
    },
    'ch9-f2': {
        'en': 'Per-call cost shown up front',
        'fr': 'Coût affiché avant chaque appel',
        'es': 'Coste por llamada mostrado de antemano',
        'ro': 'Costul per apel afișat din start',
    },
    'ch9-f3': {
        'en': 'Per-account default model',
        'fr': 'Modèle par défaut propre à chaque compte',
        'es': 'Modelo predeterminado por cuenta',
        'ro': 'Model implicit per cont',
    },
    'ch9-f4': {
        'en': 'Pay-as-you-go credits, no lock-in',
        'fr': 'Crédits à l\'usage, sans engagement',
        'es': 'Créditos de pago por uso, sin ataduras',
        'ro': 'Credite plătite la consum, fără angajament',
    },
    'ch10-title': {
        'en': 'Roles, Permissions & Visibility',
        'fr': 'Rôles, permissions et visibilité',
        'es': 'Roles, permisos y visibilidad',
        'ro': 'Roluri, permisiuni și vizibilitate',
    },
    'ch10-desc': {
        'en': 'Every application defines its own role ladder — public, member, moderator, whatever fits — and the platform enforces it consistently in the sandbox and in the generated code.',
        'fr': 'Chaque application définit sa propre échelle de rôles — public, membre, modérateur, selon vos besoins — et la plateforme l\'applique de façon cohérente dans le bac à sable comme dans le code généré.',
        'es': 'Cada aplicación define su propia escala de roles — público, miembro, moderador, lo que encaje — y la plataforma la aplica de forma coherente en el sandbox y en el código generado.',
        'ro': 'Fiecare aplicație își definește propria scară de roluri — public, membru, moderator, cum se potrivește — iar platforma o aplică consecvent în sandbox și în codul generat.',
    },
    'ch10-f1': {
        'en': 'Per-application role ladder',
        'fr': 'Échelle de rôles propre à chaque application',
        'es': 'Escala de roles por aplicación',
        'ro': 'Scară de roluri per aplicație',
    },
    'ch10-f2': {
        'en': 'Read and write access per entity and field',
        'fr': 'Accès en lecture et écriture par entité et par champ',
        'es': 'Acceso de lectura y escritura por entidad y campo',
        'ro': 'Acces de citire și scriere per entitate și câmp',
    },
    'ch10-f3': {
        'en': 'Row-level visibility rules',
        'fr': 'Règles de visibilité au niveau des enregistrements',
        'es': 'Reglas de visibilidad a nivel de registro',
        'ro': 'Reguli de vizibilitate la nivel de înregistrare',
    },
    'ch10-f4': {
        'en': 'Members only ever edit their own records',
        'fr': 'Chaque membre ne modifie que ses propres enregistrements',
        'es': 'Cada miembro solo edita sus propios registros',
        'ro': 'Membrii își editează doar propriile înregistrări',
    },
    'ch11-title': {
        'en': 'Maps & Location Data',
        'fr': 'Cartes et données de localisation',
        'es': 'Mapas y datos de ubicación',
        'ro': 'Hărți și date de localizare',
    },
    'ch11-desc': {
        'en': 'Give your application a sense of place. Location fields capture points, routes, and areas on an OpenStreetMap-backed map, ready to display and edit out of the box.',
        'fr': 'Donnez une dimension géographique à votre application. Les champs de localisation enregistrent points, itinéraires et zones sur une carte OpenStreetMap, prêts à afficher et à modifier.',
        'es': 'Da a tu aplicación un sentido del lugar. Los campos de ubicación capturan puntos, rutas y áreas en un mapa de OpenStreetMap, listos para mostrar y editar.',
        'ro': 'Oferă aplicației tale o dimensiune geografică. Câmpurile de localizare rețin puncte, trasee și zone pe o hartă OpenStreetMap, gata de afișat și editat.',
    },
    'ch11-f1': {
        'en': 'Points, itineraries, and areas',
        'fr': 'Points, itinéraires et zones',
        'es': 'Puntos, itinerarios y áreas',
        'ro': 'Puncte, itinerarii și zone',
    },
    'ch11-f2': {
        'en': 'Built-in map picker and viewer',
        'fr': 'Sélecteur et visionneuse de carte intégrés',
        'es': 'Selector y visor de mapa integrados',
        'ro': 'Selector și vizualizator de hartă integrate',
    },
    'ch11-f3': {
        'en': 'OpenStreetMap — no API key needed',
        'fr': 'OpenStreetMap — aucune clé d\'API requise',
        'es': 'OpenStreetMap: sin clave de API',
        'ro': 'OpenStreetMap — fără cheie API',
    },
    'ch11-f4': {
        'en': 'Map display mode for record lists',
        'fr': 'Mode d\'affichage carte pour les listes d\'enregistrements',
        'es': 'Modo de visualización en mapa para listas de registros',
        'ro': 'Mod de afișare hartă pentru listele de înregistrări',
    },
    # ── Data sources (SCOPE_external_data_sources.md@d2de531) ───────────────
    # Rendered between Maps and Code generation: both give an application a
    # dimension outside itself, and both are decided when the schema is.
    'ch13-title': {
        'en': 'Fill Forms From a Public Catalogue',
        'fr': 'Remplir vos formulaires depuis un catalogue public',
        'es': 'Rellena formularios desde un catálogo público',
        'ro': 'Completează formulare dintr-un catalog public',
    },
    'ch13-desc': {
        'en': 'If your application catalogues films, books, records, or products, most '
              'of what it holds already exists in a public catalogue somewhere. Declare '
              'a source once and your users fill a form from it: type a few letters, '
              'pick a result, and the fields fill in — still editable, and still saved '
              'by the ordinary form.',
        'fr': "Si votre application recense des films, des livres, des disques ou des "
              "produits, l'essentiel de son contenu existe déjà dans un catalogue "
              "public. Déclarez une source une fois et vos utilisateurs remplissent un "
              "formulaire depuis celle-ci : quelques lettres, un résultat choisi, et "
              "les champs se remplissent — toujours modifiables, et toujours "
              "enregistrés par le formulaire habituel.",
        'es': 'Si tu aplicación cataloga películas, libros, discos o productos, la mayor '
              'parte de lo que contiene ya existe en algún catálogo público. Declara una '
              'fuente una vez y tus usuarios rellenan un formulario desde ella: unas '
              'letras, un resultado elegido y los campos se rellenan — siguen siendo '
              'editables y se guardan con el formulario de siempre.',
        'ro': 'Dacă aplicația ta catalogează filme, cărți, discuri sau produse, cea mai '
              'mare parte din conținutul ei există deja într-un catalog public. Declară '
              'o sursă o dată, iar utilizatorii completează un formular din ea: câteva '
              'litere, un rezultat ales, și câmpurile se completează — rămân editabile '
              'și sunt salvate de formularul obișnuit.',
    },
    'ch13-f1': {
        'en': 'Search a public catalogue from inside a form',
        'fr': "Chercher dans un catalogue public depuis le formulaire",
        'es': 'Buscar en un catálogo público desde el formulario',
        'ro': 'Caută într-un catalog public direct din formular',
    },
    'ch13-f2': {
        'en': 'Adopt a published source, or describe your own',
        'fr': "Adopter une source publiée, ou décrire la vôtre",
        'es': 'Adopta una fuente publicada o describe la tuya',
        'ro': 'Adoptă o sursă publicată sau descrie-o pe a ta',
    },
    'ch13-f3': {
        'en': 'Suggestions only — nothing is ever saved without you',
        'fr': "Des propositions seulement — rien n'est enregistré sans vous",
        'es': 'Solo sugerencias: nada se guarda sin ti',
        'ro': 'Doar sugestii — nimic nu se salvează fără tine',
    },
    'ch13-f4': {
        'en': 'No AI runs, so no credits are spent',
        'fr': "Aucune IA ne s'exécute, aucun crédit n'est dépensé",
        'es': 'No se ejecuta ninguna IA, no se gasta ningún crédito',
        'ro': 'Nu rulează nicio IA, deci nu se consumă credite',
    },
    'ch12-title': {
        'en': 'Bring Your Own AI Agent',
        'fr': 'Utilisez votre propre agent IA',
        'es': 'Trae tu propio agente de IA',
        'ro': 'Vino cu propriul tău agent AI',
    },
    'ch12-desc': {
        'en': 'Everything the platform does is also a token-authenticated API. Point your own AI agent at it: the agent reads the live guide, declares the schema, workflow, and screens, and corrects itself against machine-readable rejections — no Migratis AI call ever fires on this lane.',
        'fr': 'Tout ce que fait la plateforme est aussi une API authentifiée par jeton. Dirigez-y votre propre agent IA : il lit le guide en ligne, déclare le schéma, le flux de travail et les écrans, et se corrige grâce à des refus lisibles par machine — aucun appel à l\'IA de Migratis n\'est déclenché sur cette voie.',
        'es': 'Todo lo que hace la plataforma es también una API autenticada por token. Dirige hacia ella tu propio agente de IA: lee la guía en vivo, declara el esquema, el flujo de trabajo y las pantallas, y se corrige con rechazos legibles por máquina — ninguna llamada a la IA de Migratis se dispara en esta vía.',
        'ro': 'Tot ce face platforma este și un API autentificat prin token. Îndreaptă-ți propriul agent AI către el: citește ghidul live, declară schema, fluxul de lucru și ecranele și se corectează singur pe baza respingerilor citibile de mașină — niciun apel AI Migratis nu pornește pe această cale.',
    },
    'ch12-f1': {
        'en': 'Token-authenticated API, with an MCP wrapper',
        'fr': 'API authentifiée par jeton, avec une surcouche MCP',
        'es': 'API autenticada por token, con un envoltorio MCP',
        'ro': 'API autentificat prin token, cu un înveliș MCP',
    },
    'ch12-f2': {
        'en': 'Self-describing guide, schema, and vocabulary',
        'fr': 'Guide, schéma et vocabulaire auto-documentés',
        'es': 'Guía, esquema y vocabulario autodescriptivos',
        'ro': 'Ghid, schemă și vocabular auto-descriptive',
    },
    'ch12-f3': {
        'en': 'Machine-readable rejections to self-correct against',
        'fr': 'Refus lisibles par machine pour s\'auto-corriger',
        'es': 'Rechazos legibles por máquina para autocorregirse',
        'ro': 'Respingeri citibile de mașină pentru auto-corectare',
    },
    'ch12-f4': {
        'en': 'Your agent builds the sandbox — only you approve it',
        'fr': 'Votre agent construit le bac à sable — vous seul l\'approuvez',
        'es': 'Tu agente construye el sandbox — solo tú lo apruebas',
        'ro': 'Agentul tău construiește sandbox-ul — doar tu îl aprobi',
    },
    'cta-title': {
        'en': 'Ready to Build Your First App?',
        'fr': 'Prêt à construire votre première application ?',
        'es': '¿Listo para construir tu primera aplicación?',
        'ro': 'Gata să construiești prima ta aplicație?',
    },
    'cta-desc': {
        'en': 'Start designing your application with AI-powered tools today.',
        'fr': 'Commencez à concevoir votre application avec des outils alimentés par l\'IA dès aujourd\'hui.',
        'es': 'Comienza a diseñar tu aplicación con herramientas impulsadas por IA hoy.',
        'ro': 'Începe să proiectezi aplicația ta cu instrumente alimentate de AI astăzi.',
    },
}

TRANSLATIONS['modal'] = {
    'close': {
        'en': 'Close',
        'fr': 'Fermer',
        'es': 'Cerrar',
        'ro': 'Închide',
    },
}

# Cross-cutting vocabulary for module-agnostic components under
# frontend/src/common/ (e.g. ExpandableText). Neutral default namespace so a
# common component never has to borrow a feature's namespace.
TRANSLATIONS['common'] = {
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
}

TRANSLATIONS['account'] = {
    'account-settings': {
        'en': 'Account settings',
        'fr': 'Paramètres du compte',
        'es': 'Configuración de la cuenta',
        'ro': 'Setări cont',
    },
    'profile': {
        'en': 'Profile',
        'fr': 'Profil',
        'es': 'Perfil',
        'ro': 'Profil',
    },
    'preferences': {
        'en': 'Preferences',
        'fr': 'Préférences',
        'es': 'Preferencias',
        'ro': 'Preferințe',
    },
    'billing': {
        'en': 'Billing',
        'fr': 'Facturation',
        'es': 'Facturación',
        'ro': 'Facturare',
    },
    # Lead-in only, and deliberately neither names the paying options nor counts
    # them: which sections appear depends on the modules the deployment
    # activated (credits, subscription, both), and what each one pays for is
    # stated by the section that owns it (`billing-credits-description` /
    # `billing-subscription-description`). Naming them here would go stale on a
    # deployment that runs only one.
    'billing-intro': {
        'en': 'Below is every paying option on your account: what it covers, and its own invoices.',
        'fr': "Voici chaque option payante de votre compte : ce qu'elle couvre et ses propres factures.",
        'es': 'A continuación, cada opción de pago de tu cuenta: qué cubre y sus propias facturas.',
        'ro': 'Mai jos, fiecare opțiune cu plată din contul tău: ce acoperă și propriile facturi.',
    },
    # NOTE: the Billing *blocks* are contributed by the modules that own them
    # (credits/shell.js, subscription/shell.js), so their copy lives in the
    # `credits` / `subscription` namespaces below — only the tab's own intro
    # stays here. See common/shell/registry.js `billingSections`.
    'language-intro': {
        'en': 'Choose your interface language. This is saved to your account.',
        'fr': "Choisissez la langue de l'interface. Ce choix est enregistré sur votre compte.",
        'es': 'Elige el idioma de la interfaz. Se guarda en tu cuenta.',
        'ro': 'Alege limba interfeței. Se salvează în contul tău.',
    },
    'language-save-failed': {
        'en': 'Could not save your language preference.',
        'fr': "Impossible d'enregistrer votre préférence de langue.",
        'es': 'No se pudo guardar tu preferencia de idioma.',
        'ro': 'Nu s-a putut salva preferința de limbă.',
    },
    'update-successful': {
        'en': 'Saved.',
        'fr': 'Enregistré.',
        'es': 'Guardado.',
        'ro': 'Salvat.',
    },
    'api-access': {
        'en': 'API access',
        'fr': 'Accès API',
        'es': 'Acceso API',
        'ro': 'Acces API',
    },
    'api-access-intro': {
        'en': 'Personal access tokens authenticate AI agents that drive the generator on your behalf. Treat them like passwords.',
        'fr': "Les jetons d'accès personnels authentifient les agents IA qui pilotent le générateur en votre nom. Traitez-les comme des mots de passe.",
        'es': 'Los tokens de acceso personal autentican a los agentes de IA que utilizan el generador en tu nombre. Trátalos como contraseñas.',
        'ro': 'Tokenurile de acces personal autentifică agenții AI care folosesc generatorul în numele tău. Tratează-le ca pe parole.',
    },
    'token-created-once': {
        'en': 'Token created. Copy it now — you will not see it again.',
        'fr': 'Jeton créé. Copiez-le maintenant — il ne sera plus affiché.',
        'es': 'Token creado. Cópialo ahora — no volverás a verlo.',
        'ro': 'Token creat. Copiază-l acum — nu îl vei mai vedea.',
    },
    'copy': {
        'en': 'Copy',
        'fr': 'Copier',
        'es': 'Copiar',
        'ro': 'Copiază',
    },
    'token-copied': {
        'en': 'Copied to clipboard.',
        'fr': 'Copié dans le presse-papiers.',
        'es': 'Copiado al portapapeles.',
        'ro': 'Copiat în clipboard.',
    },
    'token-docs-hint': {
        'en': 'Send it as an Authorization header.',
        'fr': 'Envoyez-le dans un en-tête Authorization.',
        'es': 'Envíalo como cabecera Authorization.',
        'ro': 'Trimite-l ca antet Authorization.',
    },
    'token-docs-link': {
        'en': 'Agent documentation',
        'fr': 'Documentation des agents',
        'es': 'Documentación de agentes',
        'ro': 'Documentația agenților',
    },
    'dismiss': {
        'en': 'Dismiss',
        'fr': 'Fermer',
        'es': 'Descartar',
        'ro': 'Închide',
    },
    'token-name': {
        'en': 'Token name',
        'fr': 'Nom du jeton',
        'es': 'Nombre del token',
        'ro': 'Numele tokenului',
    },
    'token-expiry-optional': {
        'en': 'Expiry (optional)',
        'fr': 'Expiration (facultatif)',
        'es': 'Caducidad (opcional)',
        'ro': 'Expirare (opțional)',
    },
    'create-token': {
        'en': 'Create token',
        'fr': 'Créer un jeton',
        'es': 'Crear token',
        'ro': 'Creează token',
    },
    'token-prefix': {
        'en': 'Prefix',
        'fr': 'Préfixe',
        'es': 'Prefijo',
        'ro': 'Prefix',
    },
    'token-last-used': {
        'en': 'Last used',
        'fr': 'Dernière utilisation',
        'es': 'Último uso',
        'ro': 'Ultima utilizare',
    },
    'token-expiry': {
        'en': 'Expiry',
        'fr': 'Expiration',
        'es': 'Caducidad',
        'ro': 'Expirare',
    },
    'token-status': {
        'en': 'Status',
        'fr': 'Statut',
        'es': 'Estado',
        'ro': 'Stare',
    },
    'token-active': {
        'en': 'Active',
        'fr': 'Actif',
        'es': 'Activo',
        'ro': 'Activ',
    },
    'token-revoked': {
        'en': 'Token revoked.',
        'fr': 'Jeton révoqué.',
        'es': 'Token revocado.',
        'ro': 'Token revocat.',
    },
    'revoke': {
        'en': 'Revoke',
        'fr': 'Révoquer',
        'es': 'Revocar',
        'ro': 'Revocă',
    },
    'no-tokens-yet': {
        'en': 'No tokens yet. Create one to connect an agent.',
        'fr': "Aucun jeton pour l'instant. Créez-en un pour connecter un agent.",
        'es': 'Aún no hay tokens. Crea uno para conectar un agente.',
        'ro': 'Încă niciun token. Creează unul pentru a conecta un agent.',
    },
    'confirm-revoke-title': {
        'en': 'Revoke token',
        'fr': 'Révoquer le jeton',
        'es': 'Revocar token',
        'ro': 'Revocă tokenul',
    },
    'confirm-revoke-text': {
        'en': 'Any agent using this token will immediately lose access. This cannot be undone.',
        'fr': "Tout agent utilisant ce jeton perdra immédiatement l'accès. Cette action est irréversible.",
        'es': 'Cualquier agente que use este token perderá el acceso de inmediato. Esto no se puede deshacer.',
        'ro': 'Orice agent care folosește acest token va pierde imediat accesul. Acțiunea este ireversibilă.',
    },
    'token-revoke-failed': {
        'en': 'Could not revoke the token.',
        'fr': 'Impossible de révoquer le jeton.',
        'es': 'No se pudo revocar el token.',
        'ro': 'Nu s-a putut revoca tokenul.',
    },
    'invalid-date': {
        'en': 'Invalid expiry date.',
        'fr': "Date d'expiration invalide.",
        'es': 'Fecha de caducidad no válida.',
        'ro': 'Dată de expirare invalidă.',
    },
    'expiry-in-past': {
        'en': 'Expiry must be in the future.',
        'fr': "L'expiration doit être dans le futur.",
        'es': 'La caducidad debe ser en el futuro.',
        'ro': 'Expirarea trebuie să fie în viitor.',
    },
    'network-error': {
        'en': 'Network error. Please try again.',
        'fr': 'Erreur réseau. Veuillez réessayer.',
        'es': 'Error de red. Inténtalo de nuevo.',
        'ro': 'Eroare de rețea. Încearcă din nou.',
    },
}


# A prune may not remove more than this share of a namespace without --force.
# Catches a half-edited source file before it empties a screen, in the manner of
# refresh_llm_pricing's MAX_SWING.
MAX_PRUNE_SHARE = 0.25


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
        parser.add_argument(
            '--prune',
            action='store_true',
            help='Report keys this file no longer declares (add --apply to remove them).',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='With --prune: actually unlink/delete, instead of reporting.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='With --prune --apply: proceed past the share guard.',
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

        # ------------------------------------------------------------------ #
        # 3. Prune — the other half of seeding, and the dangerous half
        # ------------------------------------------------------------------ #
        if options['prune']:
            self._prune(only_ns, apply=options['apply'], force=options['force'])

    # ---------------------------------------------------------------------- #
    # Prune
    # ---------------------------------------------------------------------- #
    def _prune(self, only_ns, *, apply=False, force=False):
        """Retire keys this file no longer declares.

        Seeding is additive, so a key that was renamed six months ago is still in
        the database, still served by `GET /i18n/…`, and still sitting in the
        admin looking like something a translator should maintain. Nothing ever
        told those apart from the live set.

        Three rules hold this down, and each of them exists because the obvious
        implementation is destructive:

        * **Only namespaces this file declares.** A generated application seeds
          its own namespace with its own `seed_<module>` command, into these same
          tables. Walking every namespace would delete an installed app's entire
          vocabulary on the first run — the same byte-copy destructiveness that
          keeps this file out of the base sync — and the owner would have no way
          to tell what happened. An undeclared namespace is not reported either:
          reporting it invites someone to clean it up by hand.
        * **Unlink first; delete only what is left with no namespace at all.** A
          key can belong to several namespaces, and dropping it from one is
          retiring a label from one screen, not deleting it from the product.
        * **Report by default; `--apply` writes.** A half-edited source file
          looks exactly like a deliberate cleanup, and the difference is several
          hundred rows users can see. The share guard below is the sibling of
          `refresh_llm_pricing`'s MAX_SWING and `refresh_routing_regions`'
          retire share.
        """
        namespaces = sorted(set(TRANSLATIONS) | set(NAMESPACE_LINKS))
        if only_ns:
            namespaces = [only_ns]

        total_unlinked = total_deleted = 0
        for ns_name in namespaces:
            declared = set(TRANSLATIONS.get(ns_name, {})) | set(NAMESPACE_LINKS.get(ns_name, []))
            ns_obj = TranslationNameSpace.objects.filter(ns=ns_name).first()
            if ns_obj is None:
                continue

            stored = list(TranslationKey.objects.filter(ns=ns_obj))
            orphans = [k for k in stored if k.key not in declared]
            if not orphans:
                continue

            share = len(orphans) / len(stored)
            self.stdout.write(self.style.WARNING(
                f"  '{ns_name}': {len(orphans)} of {len(stored)} keys are no longer "
                f"declared ({share:.0%})"))
            for key_obj in orphans:
                self.stdout.write(f'    - {key_obj.key}')

            if not apply:
                continue
            if share > MAX_PRUNE_SHARE and not force:
                self.stdout.write(self.style.ERROR(
                    f"  Refused: pruning would remove {share:.0%} of '{ns_name}', over "
                    f'the {MAX_PRUNE_SHARE:.0%} guard. A half-edited source file looks '
                    f'exactly like this. Re-run with --force if the cleanup is real.'))
                continue

            for key_obj in orphans:
                key_obj.ns.remove(ns_obj)
                total_unlinked += 1
                if not key_obj.ns.exists():
                    # No namespace left anywhere: nothing serves it and nothing
                    # can. Its texts go with it (FK cascade).
                    key_obj.delete()
                    total_deleted += 1

        if apply:
            self.stdout.write(self.style.SUCCESS(
                f'Pruned.\n'
                f'  Keys unlinked:  {total_unlinked}\n'
                f'  Keys deleted:   {total_deleted} (those left in no namespace at all)'))
        else:
            self.stdout.write('Prune report only — re-run with --apply to remove them.')



# ===========================================================================
# add-on module namespaces (user / subscription / support) — auto-seeded
# ===========================================================================
TRANSLATIONS['login'] = {
    'fields-mandatory': {
        'en': 'Fields marked with',
        'fr': 'Champs marqués',
        'es': 'Campos marcados',
        'ro': 'Câmpuri marcate',
    },
    'email': {
        'en': 'Email',
        'fr': 'Email',
        'es': 'Correo electrónico',
        'ro': 'Email',
    },
    'password': {
        'en': 'Password',
        'fr': 'Mot de passe',
        'es': 'Contraseña',
        'ro': 'Parolă',
    },
    'validate': {
        'en': 'Validate',
        'fr': 'Valider',
        'es': 'Validar',
        'ro': 'Validează',
    },
    'reset-password': {
        'en': 'Reset password',
        'fr': 'Réinitialiser le mot de passe',
        'es': 'Restablecer contraseña',
        'ro': 'Resetează parola',
    },
    'no-account-register': {
        'en': "Don't have an account? Register",
        'fr': "Pas de compte ? S'inscrire",
        'es': '¿No tienes cuenta? Regístrate',
        'ro': 'Nu ai cont? Înregistrează-te',
    },
    'login-successfull': {
        'en': 'Login successful',
        'fr': 'Connexion réussie',
        'es': 'Inicio de sesión exitoso',
        'ro': 'Autentificare reușită',
    },
    'account-deleted': {
        'en': 'Account deleted',
        'fr': 'Compte supprimé',
        'es': 'Cuenta eliminada',
        'ro': 'Cont șters',
    },
    'error-occured': {
        'en': 'An error occurred',
        'fr': 'Une erreur est survenue',
        'es': 'Ha ocurrido un error',
        'ro': 'A apărut o eroare',
    },
    'empty-field': {
        'en': 'This field cannot be empty',
        'fr': 'Ce champ ne peut pas être vide',
        'es': 'Este campo no puede estar vacío',
        'ro': 'Acest câmp nu poate fi gol',
    },
    'max-length-exceeded': {
        'en': 'Maximum length exceeded',
        'fr': 'Longueur maximale dépassée',
        'es': 'Longitud máxima excedida',
        'ro': 'Lungimea maximă depășită',
    },
    'email-invalid': {
        'en': 'Invalid email address',
        'fr': 'Adresse email invalide',
        'es': 'Dirección de correo inválida',
        'ro': 'Adresă de email invalidă',
    },
    'tfa-enter-code': {
        'en': 'Enter the code sent to your email',
        'fr': 'Entrez le code envoyé à votre email',
        'es': 'Ingrese el código enviado a su correo',
        'ro': 'Introdu codul trimis pe email',
    },
    'tfa-code': {
        'en': 'Security code',
        'fr': 'Code de sécurité',
        'es': 'Código de seguridad',
        'ro': 'Cod de securitate',
    },
    'tfa-resend-code': {
        'en': 'Resend code',
        'fr': 'Renvoyer le code',
        'es': 'Reenviar código',
        'ro': 'Retrimite codul',
    },
    'tfa-back': {
        'en': 'Back',
        'fr': 'Retour',
        'es': 'Volver',
        'ro': 'Înapoi',
    },
    'tfa-code-required': {
        'en': 'TFA code is required',
        'fr': 'Le code TFA est requis',
        'es': 'Se requiere código TFA',
        'ro': 'Codul TFA este obligatoriu',
    },
    'tfa-code-invalid': {
        'en': 'Invalid TFA code',
        'fr': 'Code TFA invalide',
        'es': 'Código TFA inválido',
        'ro': 'Cod TFA invalid',
    },
    'tfa-code-expired': {
        'en': 'TFA code has expired, please request a new one',
        'fr': 'Le code TFA a expiré, veuillez en demander un nouveau',
        'es': 'El código TFA ha expirado, por favor solicita uno nuevo',
        'ro': 'Codul TFA a expirat, te rugăm să ceri unul nou',
    },
    'tfa-max-attempts': {
        'en': 'Too many attempts, please request a new TFA code',
        'fr': 'Trop de tentatives, veuillez demander un nouveau code TFA',
        'es': 'Demasiados intentos, por favor solicita un nuevo código TFA',
        'ro': 'Prea multe încercări, te rugăm să ceri un nou cod TFA',
    },
    'tfa-code-sent': {
        'en': 'TFA code sent to your email',
        'fr': 'Code TFA envoyé à votre email',
        'es': 'Código TFA enviado a tu correo',
        'ro': 'Codul TFA a fost trimis pe email',
    },
    'tfa-resend-rate-limit': {
        'en': 'Please wait before requesting a new TFA code',
        'fr': 'Veuillez attendre avant de demander un nouveau code TFA',
        'es': 'Por favor espera antes de solicitar un nuevo código TFA',
        'ro': 'Te rugăm să aștepți înainte de a cere un nou cod TFA',
    },
    'remember-device': {
        'en': 'Remember this device for 1 week',
        'fr': 'Se souvenir de cet appareil pendant 1 semaine',
        'es': 'Recordar este dispositivo durante 1 semana',
        'ro': 'Ține minte acest dispozitiv timp de 1 săptămână',
    },
    'user-unknown-or-wrong-credentials': {
        'en': 'Unknown user or wrong credentials',
        'fr': 'Utilisateur inconnu ou identifiants incorrects',
        'es': 'Usuario desconocido o credenciales incorrectas',
        'ro': 'Utilizator necunoscut sau credențiale incorecte',
    },
    'registration-success': {
        'en': 'Registration successful',
        'fr': 'Inscription réussie',
        'es': 'Registro exitoso',
        'ro': 'Înregistrare reușită',
    },
    'tfa-email-send-failed': {
        'en': 'We could not send your verification code. Please try again in a moment.',
        'fr': "Nous n'avons pas pu envoyer votre code de vérification. Veuillez réessayer dans un instant.",
        'es': 'No hemos podido enviar tu código de verificación. Inténtalo de nuevo en un momento.',
        'ro': 'Nu am putut trimite codul de verificare. Vă rugăm să încercați din nou într-un moment.',
    },
}

TRANSLATIONS['register'] = {
    'register': {
        'en': 'Register',
        'fr': "S'inscrire",
        'es': 'Registrarse',
        'ro': 'Înregistrare',
    },
    # LinkToCguv — the terms-of-service line next to the download link.
    'link-to-cgu': {
        'en': 'I accept the terms and conditions',
        'fr': "J'accepte les conditions générales",
        'es': 'Acepto los términos y condiciones',
        'ro': 'Accept termenii și condițiile',
    },
    'download-cgu': {
        'en': 'Download the terms and conditions',
        'fr': 'Télécharger les conditions générales',
        'es': 'Descargar los términos y condiciones',
        'ro': 'Descărcați termenii și condițiile',
    },
}

TRANSLATIONS['profile'] = {
    'profile': {
        'en': 'Profile',
        'fr': 'Profil',
        'es': 'Perfil',
        'ro': 'Profil',
    },
    'your-informations': {
        'en': 'Your information',
        'fr': 'Vos informations',
        'es': 'Tu información',
        'ro': 'Informațiile tale',
    },
    'delete-profile': {
        'en': 'Delete profile',
        'fr': 'Supprimer le profil',
        'es': 'Eliminar perfil',
        'ro': 'Șterge profilul',
    },
    'password-change': {
        'en': 'Change password',
        'fr': 'Changer le mot de passe',
        'es': 'Cambiar contraseña',
        'ro': 'Schimbă parola',
    },
    'confirm-remove-profile': {
        'en': 'Confirm profile deletion',
        'fr': 'Confirmer la suppression du profil',
        'es': 'Confirmar la eliminación del perfil',
        'ro': 'Confirmă ștergerea profilului',
    },
    'remove-profile-text': {
        'en': 'Are you sure you want to delete your profile? This action is irreversible.',
        'fr': 'Êtes-vous sûr de vouloir supprimer votre profil ? Cette action est irréversible.',
        'es': '¿Estás seguro de que quieres eliminar tu perfil? Esta acción es irreversible.',
        'ro': 'Sigur doriți să vă ștergeți profilul? Această acțiune este ireversibilă.',
    },
    'remove-profile-subscription-text': {
        'en': 'Your active subscription will be cancelled and you will lose access.',
        'fr': 'Votre abonnement actif sera annulé et vous perdrez votre accès.',
        'es': 'Tu suscripción activa se cancelará y perderás el acceso.',
        'ro': 'Abonamentul dvs. activ va fi anulat și veți pierde accesul.',
    },
}

TRANSLATIONS['password'] = {
    # PasswordValidation checklist — one line per rule, shown live under the
    # password fields on register / reset / set-password. The length figure
    # matches the `requiredLength` that component passes (10), which is
    # stricter than Django's MinimumLengthValidator (8) on purpose.
    'password-length': {
        'en': 'At least 10 characters',
        'fr': 'Au moins 10 caractères',
        'es': 'Al menos 10 caracteres',
        'ro': 'Cel puțin 10 caractere',
    },
    'password-number': {
        'en': 'At least one number',
        'fr': 'Au moins un chiffre',
        'es': 'Al menos un número',
        'ro': 'Cel puțin o cifră',
    },
    'password-uppercase': {
        'en': 'At least one uppercase letter',
        'fr': 'Au moins une lettre majuscule',
        'es': 'Al menos una letra mayúscula',
        'ro': 'Cel puțin o literă mare',
    },
    'password-lowercase': {
        'en': 'At least one lowercase letter',
        'fr': 'Au moins une lettre minuscule',
        'es': 'Al menos una letra minúscula',
        'ro': 'Cel puțin o literă mică',
    },
    'password-special-characters': {
        'en': 'At least one special character',
        'fr': 'Au moins un caractère spécial',
        'es': 'Al menos un carácter especial',
        'ro': 'Cel puțin un caracter special',
    },
    'password-match': {
        'en': 'Passwords match',
        'fr': 'Les mots de passe correspondent',
        'es': 'Las contraseñas coinciden',
        'ro': 'Parolele se potrivesc',
    },
    'change-password': {
        'en': 'Change password',
        'fr': 'Changer le mot de passe',
        'es': 'Cambiar contraseña',
        'ro': 'Schimbă parola',
    },
    'old-password': {
        'en': 'Current password',
        'fr': 'Mot de passe actuel',
        'es': 'Contraseña actual',
        'ro': 'Parola actuală',
    },
    'password': {
        'en': 'Password',
        'fr': 'Mot de passe',
        'es': 'Contraseña',
        'ro': 'Parolă',
    },
    'confirm-password': {
        'en': 'Confirm password',
        'fr': 'Confirmer le mot de passe',
        'es': 'Confirmar contraseña',
        'ro': 'Confirmă parola',
    },
    'empty-field': {
        'en': 'This field cannot be empty',
        'fr': 'Ce champ ne peut pas être vide',
        'es': 'Este campo no puede estar vacío',
        'ro': 'Acest câmp nu poate fi gol',
    },
    'fields-mandatory': {
        'en': 'Fields marked with * are mandatory',
        'fr': "Les champs marqués d'un * sont obligatoires",
        'es': 'Los campos marcados con * son obligatorios',
        'ro': 'Câmpurile marcate cu * sunt obligatorii',
    },
    'validate': {
        'en': 'Validate',
        'fr': 'Valider',
        'es': 'Validar',
        'ro': 'Validează',
    },
    'error-occured': {
        'en': 'An error occurred. Please try again.',
        'fr': 'Une erreur est survenue. Veuillez réessayer.',
        'es': 'Ha ocurrido un error. Inténtalo de nuevo.',
        'ro': 'A apărut o eroare. Încercați din nou.',
    },
}

TRANSLATIONS['reset'] = {
    'reset-password': {
        'en': 'Reset password',
        'fr': 'Réinitialiser le mot de passe',
        'es': 'Restablecer contraseña',
        'ro': 'Resetează parola',
    },
    'email': {
        'en': 'Email',
        'fr': 'Email',
        'es': 'Correo electrónico',
        'ro': 'Email',
    },
    'email-invalid': {
        'en': 'Invalid email address',
        'fr': 'Adresse email invalide',
        'es': 'Dirección de correo inválida',
        'ro': 'Adresă de email invalidă',
    },
    'help-change-password': {
        'en': 'Enter your email address and we will send you a link to reset your password.',
        'fr': 'Saisissez votre adresse email et nous vous enverrons un lien pour réinitialiser votre mot de passe.',
        'es': 'Introduce tu dirección de correo y te enviaremos un enlace para restablecer tu contraseña.',
        'ro': 'Introduceți adresa de email și vă vom trimite un link pentru resetarea parolei.',
    },
    'fields-mandatory': {
        'en': 'Fields marked with * are mandatory',
        'fr': "Les champs marqués d'un * sont obligatoires",
        'es': 'Los campos marcados con * son obligatorios',
        'ro': 'Câmpurile marcate cu * sunt obligatorii',
    },
    'validate': {
        'en': 'Validate',
        'fr': 'Valider',
        'es': 'Validar',
        'ro': 'Validează',
    },
    'error-occured': {
        'en': 'An error occurred. Please try again.',
        'fr': 'Une erreur est survenue. Veuillez réessayer.',
        'es': 'Ha ocurrido un error. Inténtalo de nuevo.',
        'ro': 'A apărut o eroare. Încercați din nou.',
    },
}

TRANSLATIONS['invitation'] = {
    'complete-invitation': {
        'en': 'Complete your registration',
        'fr': 'Complétez votre inscription',
        'es': 'Completa tu registro',
        'ro': 'Finalizați înregistrarea',
    },
}

TRANSLATIONS['userform'] = {
    'payment-service-unavailable': {
        'en': 'The payment service is temporarily unavailable — please try again later.',
        'fr': 'Le service de paiement est temporairement indisponible — veuillez réessayer plus tard.',
        'es': 'El servicio de pago no está disponible temporalmente. Inténtalo de nuevo más tarde.',
        'ro': 'Serviciul de plată este temporar indisponibil — încercați din nou mai târziu.',
    },
    'taxnumber-invalid': {
        'en': 'The tax number was refused by the payment service.',
        'fr': 'Le numéro de TVA a été refusé par le service de paiement.',
        'es': 'El número fiscal fue rechazado por el servicio de pago.',
        'ro': 'Codul fiscal a fost respins de serviciul de plată.',
    },
    'payment-config-error': {
        'en': 'Payment could not be started because of a configuration problem. Please contact support.',
        'fr': "Le paiement n'a pas pu démarrer en raison d'un problème de configuration. Veuillez contacter le support.",
        'es': 'No se pudo iniciar el pago debido a un problema de configuración. Ponte en contacto con soporte.',
        'ro': 'Plata nu a putut fi inițiată din cauza unei probleme de configurare. Contactați asistența.',
    },
    'error-occured': {
        'en': 'An error occurred. Please try again.',
        'fr': "Une erreur s'est produite. Veuillez réessayer.",
        'es': 'Se produjo un error. Inténtalo de nuevo.',
        'ro': 'A apărut o eroare. Încercați din nou.',
    },
    # The birthdate picker used to render with no label at all — legible only
    # because it sat alone under a labelled field. It shares a row now, so it
    # has to name itself.
    'birthdate': {
        'en': 'Date of birth',
        'fr': 'Date de naissance',
        'es': 'Fecha de nacimiento',
        'ro': 'Data nașterii',
    },
}

TRANSLATIONS['upload'] = {
    'upload': {
        'en': 'Upload',
        'fr': 'Télécharger',
        'es': 'Subir',
        'ro': 'Încărcare',
    },
    'upload-file': {
        'en': 'Upload file',
        'fr': 'Télécharger un fichier',
        'es': 'Subir archivo',
        'ro': 'Încărcare fișier',
    },
    'select-file': {
        'en': 'Select file',
        'fr': 'Sélectionner un fichier',
        'es': 'Seleccionar archivo',
        'ro': 'Selectează fișier',
    },
    'upload-support-help': {
        'en': 'You can upload images, PDFs or documents (max 10MB)',
        'fr': 'Vous pouvez télécharger des images, PDF ou documents (max 10Mo)',
        'es': 'Puede subir imágenes, PDF o documentos (máx 10MB)',
        'ro': 'Puteți încărca imagini, PDF sau documente (max 10MB)',
    },
}

TRANSLATIONS['subscription'] = {
    # Account → Billing block (SubscriptionBilling), contributed through the
    # shell registry's `billingSections` slot — the heading moved off the
    # `account` namespace with the component so the module stays self-contained.
    'billing-subscription-title': {
        'en': 'Subscription',
        'fr': 'Abonnement',
        'es': 'Suscripción',
        'ro': 'Abonament',
    },
    # What a plan covers, opposite the credits column. Deliberately generic: a
    # deployment that meters something specific should say so here.
    'billing-subscription-description': {
        'en': 'A subscription gives you ongoing access for the period you '
              'choose, renewed automatically until you cancel. It is billed per '
              'period and does not replace credits: metered operations are '
              'still charged in credits as you use them.',
        'fr': "Un abonnement vous donne un accès continu pour la période "
              "choisie, renouvelé automatiquement jusqu'à résiliation. Il est "
              "facturé par période et ne remplace pas les crédits : les "
              "opérations décomptées restent facturées en crédits au fur et à "
              "mesure de leur utilisation.",
        'es': 'Una suscripción te da acceso continuo durante el periodo que '
              'elijas, renovado automáticamente hasta que la canceles. Se '
              'factura por periodo y no sustituye a los créditos: las '
              'operaciones medidas se siguen cobrando en créditos según las '
              'usas.',
        'ro': 'Un abonament îți oferă acces continuu pe perioada aleasă, '
              'reînnoit automat până la anulare. Se facturează per perioadă și '
              'nu înlocuiește creditele: operațiunile contorizate se taxează '
              'tot în credite, pe măsură ce le folosești.',
    },
    'plans': {
        'en': 'Plans',
        'fr': 'Forfaits',
        'es': 'Planes',
        'ro': 'Planuri',
    },
    'pricing': {
        'en': 'Pricing',
        'fr': 'Tarifs',
        'es': 'Precios',
        'ro': 'Prețuri',
    },
    'label': {
        'en': 'Plan',
        'fr': 'Formule',
        'es': 'Plan',
        'ro': 'Plan',
    },
    'plan': {
        'en': 'Plan',
        'fr': 'Forfait',
        'es': 'Plan',
        'ro': 'Plan',
    },
    'price': {
        'en': 'Price',
        'fr': 'Prix',
        'es': 'Precio',
        'ro': 'Preț',
    },
    'ttc': {
        'en': 'incl. tax',
        'fr': 'TTC',
        'es': 'IVA incl.',
        'ro': 'cu TVA',
    },
    'vat': {
        'en': 'VAT',
        'fr': 'TVA',
        'es': 'IVA',
        'ro': 'TVA',
    },
    'of': {
        'en': 'of',
        'fr': 'du',
        'es': 'del',
        'ro': 'din',
    },
    'paid': {
        'en': 'Paid',
        'fr': 'Payé',
        'es': 'Pagado',
        'ro': 'Plătit',
    },
    'unpaid': {
        'en': 'Unpaid',
        'fr': 'Impayé',
        'es': 'No pagado',
        'ro': 'Neplătit',
    },
    'no-plans-for-the-moment': {
        'en': 'No plans available at the moment.',
        'fr': 'Aucun forfait disponible pour le moment.',
        'es': 'No hay planes disponibles por el momento.',
        'ro': 'Niciun plan disponibil momentan.',
    },
    'normal-subscription': {
        'en': 'Subscribe to unlock full access.',
        'fr': "Abonnez-vous pour débloquer l'accès complet.",
        'es': 'Suscríbete para desbloquear el acceso completo.',
        'ro': 'Abonează-te pentru a debloca accesul complet.',
    },
    'trial-subscription': {
        'en': 'Start your free trial.',
        'fr': 'Démarrez votre essai gratuit.',
        'es': 'Comienza tu prueba gratuita.',
        'ro': 'Începe perioada de probă gratuită.',
    },
    'trial-explanation': {
        'en': "Start with a free trial — you won't be charged until it ends, and you can cancel anytime.",
        'fr': "Commencez par un essai gratuit — vous ne serez débité qu'à la fin de l'essai, et vous pouvez annuler à tout moment.",
        'es': 'Empieza con una prueba gratuita: no se te cobrará hasta que termine y puedes cancelar cuando quieras.',
        'ro': 'Începe cu o perioadă de probă gratuită — nu vei fi taxat până la finalul acesteia și poți anula oricând.',
    },
    'trial-period': {
        'en': 'Trial period',
        'fr': "Période d'essai",
        'es': 'Periodo de prueba',
        'ro': 'Perioadă de probă',
    },
    'with-trial': {
        'en': '(with free trial)',
        'fr': '(avec essai gratuit)',
        'es': '(con prueba gratuita)',
        'ro': '(cu probă gratuită)',
    },
    'try': {
        'en': 'Try',
        'fr': 'Essayer',
        'es': 'Probar',
        'ro': 'Încearcă',
    },
    'pay': {
        'en': 'Pay',
        'fr': 'Payer',
        'es': 'Pagar',
        'ro': 'Plătește',
    },
    'subscribe': {
        'en': 'Subscribe',
        'fr': "S'abonner",
        'es': 'Suscribirse',
        'ro': 'Abonează-te',
    },
    'proceed-to-payment': {
        'en': 'Proceed to payment',
        'fr': 'Procéder au paiement',
        'es': 'Proceder al pago',
        'ro': 'Continuă la plată',
    },
    'select-plan': {
        'en': 'Select a plan',
        'fr': 'Sélectionnez un forfait',
        'es': 'Selecciona un plan',
        'ro': 'Selectează un plan',
    },
    'secure-payment': {
        'en': 'Secure payment',
        'fr': 'Paiement sécurisé',
        'es': 'Pago seguro',
        'ro': 'Plată securizată',
    },
    'secure-zone': {
        'en': 'Secure zone',
        'fr': 'Zone sécurisée',
        'es': 'Zona segura',
        'ro': 'Zonă securizată',
    },
    'stripe-powered': {
        'en': 'Payments powered by Stripe',
        'fr': 'Paiements propulsés par Stripe',
        'es': 'Pagos con tecnología de Stripe',
        'ro': 'Plăți oferite de Stripe',
    },
    'accepted-cards': {
        'en': 'Accepted cards',
        'fr': 'Cartes acceptées',
        'es': 'Tarjetas aceptadas',
        'ro': 'Carduri acceptate',
    },
    'no-subscription': {
        'en': 'No active subscription',
        'fr': 'Aucun abonnement actif',
        'es': 'Sin suscripción activa',
        'ro': 'Niciun abonament activ',
    },
    'your-subscription': {
        'en': 'Your subscription',
        'fr': 'Votre abonnement',
        'es': 'Tu suscripción',
        'ro': 'Abonamentul tău',
    },
    'current-subscription': {
        'en': 'Current subscription',
        'fr': 'Abonnement actuel',
        'es': 'Suscripción actual',
        'ro': 'Abonament curent',
    },
    'cancelled-subscription': {
        'en': 'Cancelled subscription',
        'fr': 'Abonnement annulé',
        'es': 'Suscripción cancelada',
        'ro': 'Abonament anulat',
    },
    'access-until': {
        'en': 'Access until',
        'fr': "Accès jusqu'au",
        'es': 'Acceso hasta',
        'ro': 'Acces până la',
    },
    'first-payment-at': {
        'en': 'First payment on',
        'fr': 'Premier paiement le',
        'es': 'Primer pago el',
        'ro': 'Prima plată la',
    },
    'automatic-renewal-at': {
        'en': 'Automatic renewal on',
        'fr': 'Renouvellement automatique le',
        'es': 'Renovación automática el',
        'ro': 'Reînnoire automată la',
    },
    'change-subscription': {
        'en': 'Change subscription',
        'fr': "Changer d'abonnement",
        'es': 'Cambiar suscripción',
        'ro': 'Schimbă abonamentul',
    },
    'unsubscribe': {
        'en': 'Cancel subscription',
        'fr': "Résilier l'abonnement",
        'es': 'Cancelar suscripción',
        'ro': 'Anulează abonamentul',
    },
    'reactivate-subscription': {
        'en': 'Reactivate subscription',
        'fr': "Réactiver l'abonnement",
        'es': 'Reactivar suscripción',
        'ro': 'Reactivează abonamentul',
    },
    'confirm-unsubscribe': {
        'en': 'Are you sure you want to cancel your subscription?',
        'fr': 'Êtes-vous sûr de vouloir résilier votre abonnement ?',
        'es': '¿Seguro que quieres cancelar tu suscripción?',
        'ro': 'Sigur vrei să anulezi abonamentul?',
    },
    'confirm-reactivate-subscription': {
        'en': 'Are you sure you want to reactivate your subscription?',
        'fr': 'Êtes-vous sûr de vouloir réactiver votre abonnement ?',
        'es': '¿Seguro que quieres reactivar tu suscripción?',
        'ro': 'Sigur vrei să reactivezi abonamentul?',
    },
    'confirm-change-subscription': {
        'en': 'Are you sure you want to change your subscription?',
        'fr': "Êtes-vous sûr de vouloir changer d'abonnement ?",
        'es': '¿Seguro que quieres cambiar tu suscripción?',
        'ro': 'Sigur vrei să schimbi abonamentul?',
    },
    'help-confirm-unsubscribe': {
        'en': 'You will keep access until the end of the current period.',
        'fr': "Vous conserverez l'accès jusqu'à la fin de la période en cours.",
        'es': 'Conservarás el acceso hasta el final del periodo actual.',
        'ro': 'Vei păstra accesul până la sfârșitul perioadei curente.',
    },
    'help-confirm-reactivate-subscription': {
        'en': 'Your subscription will continue and renew automatically.',
        'fr': 'Votre abonnement continuera et se renouvellera automatiquement.',
        'es': 'Tu suscripción continuará y se renovará automáticamente.',
        'ro': 'Abonamentul tău va continua și se va reînnoi automat.',
    },
    'help-change-subscription': {
        'en': 'Your new plan takes effect at the next renewal.',
        'fr': 'Votre nouveau forfait prend effet au prochain renouvellement.',
        'es': 'Tu nuevo plan entra en vigor en la próxima renovación.',
        'ro': 'Noul tău plan intră în vigoare la următoarea reînnoire.',
    },
    'your-invoices': {
        'en': 'Your invoices',
        'fr': 'Vos factures',
        'es': 'Tus facturas',
        'ro': 'Facturile tale',
    },
    'download-invoice': {
        'en': 'Download invoice',
        'fr': 'Télécharger la facture',
        'es': 'Descargar factura',
        'ro': 'Descarcă factura',
    },
    'validate': {
        'en': 'Confirm',
        'fr': 'Valider',
        'es': 'Confirmar',
        'ro': 'Confirmă',
    },
    'subscription-success': {
        'en': 'Subscription successful.',
        'fr': 'Abonnement réussi.',
        'es': 'Suscripción realizada correctamente.',
        'ro': 'Abonament realizat cu succes.',
    },
    'subscription-error': {
        'en': 'Subscription error. Please try again.',
        'fr': "Erreur d'abonnement. Veuillez réessayer.",
        'es': 'Error de suscripción. Inténtalo de nuevo.',
        'ro': 'Eroare de abonament. Încearcă din nou.',
    },
    'payment-service-unavailable': {
        'en': 'The payment service is temporarily unavailable — please try again later.',
        'fr': 'Le service de paiement est temporairement indisponible — veuillez réessayer plus tard.',
        'es': 'El servicio de pago no está disponible temporalmente. Inténtalo de nuevo más tarde.',
        'ro': 'Serviciul de plată este temporar indisponibil — încercați din nou mai târziu.',
    },
    'taxnumber-invalid': {
        'en': 'The tax number was refused by the payment service.',
        'fr': 'Le numéro de TVA a été refusé par le service de paiement.',
        'es': 'El número fiscal fue rechazado por el servicio de pago.',
        'ro': 'Codul fiscal a fost respins de serviciul de plată.',
    },
    'payment-config-error': {
        'en': 'Payment could not be started because of a configuration problem. Please contact support.',
        'fr': "Le paiement n'a pas pu démarrer en raison d'un problème de configuration. Veuillez contacter le support.",
        'es': 'No se pudo iniciar el pago debido a un problema de configuración. Ponte en contacto con soporte.',
        'ro': 'Plata nu a putut fi inițiată din cauza unei probleme de configurare. Contactați asistența.',
    },
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

# billing — shared payment engine (stripe_payment app). Error/label keys the
# unified /billing/* endpoints and the subscribe flow answer with.
TRANSLATIONS['billing'] = {
    'payment-service-unavailable': {
        'en': 'The payment service is temporarily unavailable — please try again later.',
        'fr': 'Le service de paiement est temporairement indisponible — veuillez réessayer plus tard.',
        'es': 'El servicio de pago no está disponible temporalmente. Inténtalo de nuevo más tarde.',
        'ro': 'Serviciul de plată este temporar indisponibil — încercați din nou mai târziu.',
    },
    'taxnumber-invalid': {
        'en': 'The tax number was refused by the payment service.',
        'fr': 'Le numéro de TVA a été refusé par le service de paiement.',
        'es': 'El número fiscal fue rechazado por el servicio de pago.',
        'ro': 'Codul fiscal a fost respins de serviciul de plată.',
    },
    'payment-config-error': {
        'en': 'Payment could not be started because of a configuration problem. Please contact support.',
        'fr': "Le paiement n'a pas pu démarrer en raison d'un problème de configuration. Veuillez contacter le support.",
        'es': 'No se pudo iniciar el pago debido a un problema de configuración. Ponte en contacto con soporte.',
        'ro': 'Plata nu a putut fi inițiată din cauza unei probleme de configurare. Contactați asistența.',
    },
    'payment-failed': {
        'en': 'Payment could not be started. Please try again.',
        'fr': "Le paiement n'a pas pu démarrer. Veuillez réessayer.",
        'es': 'No se pudo iniciar el pago. Inténtalo de nuevo.',
        'ro': 'Plata nu a putut fi inițiată. Încercați din nou.',
    },
    'invalid-purpose': {
        'en': 'Unknown payment type.',
        'fr': 'Type de paiement inconnu.',
        'es': 'Tipo de pago desconocido.',
        'ro': 'Tip de plată necunoscut.',
    },
    'invalid-tier': {
        'en': 'Invalid package selected.',
        'fr': 'Forfait sélectionné invalide.',
        'es': 'Paquete seleccionado no válido.',
        'ro': 'Pachet selectat invalid.',
    },
    'minimum-quantity': {
        'en': 'The minimum quantity is {{min}}.',
        'fr': 'La quantité minimale est {{min}}.',
        'es': 'La cantidad mínima es {{min}}.',
        'ro': 'Cantitatea minimă este {{min}}.',
    },
    'payment-cancelled': {
        'en': 'Payment cancelled.',
        'fr': 'Paiement annulé.',
        'es': 'Pago cancelado.',
        'ro': 'Plată anulată.',
    },
    'payment-success': {
        'en': 'Payment successful.',
        'fr': 'Paiement réussi.',
        'es': 'Pago realizado con éxito.',
        'ro': 'Plată efectuată cu succes.',
    },
    # Invoice-line label for a credits purchase. MUST be a distinct key from the
    # `credits` key (credits ns = 'Credits available: {{remaining}}') — i18n keys
    # are global, so reusing 'credits' here would render the interpolated balance
    # template on invoices instead of a purchase label.
    'credits-purchase': {
        'en': 'Credit purchase',
        'fr': 'Achat de crédits',
        'es': 'Compra de créditos',
        'ro': 'Achiziție de credite',
    },
    # Empty state of common/components/InvoiceList — each Billing column lists
    # only its own receipts, so one of the two is routinely empty.
    'no-invoices': {
        'en': 'No invoices yet.',
        'fr': 'Aucune facture pour le moment.',
        'es': 'Todavía no hay facturas.',
        'ro': 'Încă nicio factură.',
    },
}

# ── credits (migratis.credits) ─────────────────────────────────────────────
# De-AI'd credit widget / purchase-modal copy. The credits FE module resolves
# from `credits` + `billing` only.
TRANSLATIONS['credits'] = {
    # Account → Billing block (CreditsBilling), contributed through the shell
    # registry's `billingSections` slot — the copy moved off the `account`
    # namespace with the component so the module stays self-contained.
    'billing-credits-title': {
        'en': 'Credits',
        'fr': 'Crédits',
        'es': 'Créditos',
        'ro': 'Credite',
    },
    # What the column is for, opposite the subscription column. Deliberately
    # generic: a deployment that meters something specific should say so here.
    'billing-credits-description': {
        'en': 'Credits are pay-as-you-go: they are consumed by the metered '
              'operations of the service, and the cost of an operation is shown '
              'before you confirm it. Credits never expire, and buying them '
              'does not require a subscription.',
        'fr': "Les crédits fonctionnent à l'usage : ils sont consommés par les "
              "opérations décomptées du service, et le coût d'une opération "
              "vous est indiqué avant confirmation. Les crédits n'expirent pas "
              "et leur achat ne nécessite aucun abonnement.",
        'es': 'Los créditos son de pago por uso: los consumen las operaciones '
              'medidas del servicio, y el coste de una operación se muestra '
              'antes de confirmarla. Los créditos no caducan y comprarlos no '
              'requiere suscripción.',
        'ro': 'Creditele se plătesc la consum: sunt consumate de operațiunile '
              'contorizate ale serviciului, iar costul unei operațiuni îți este '
              'afișat înainte de confirmare. Creditele nu expiră, iar '
              'cumpărarea lor nu necesită abonament.',
    },
    'billing-credits-balance': {
        'en': 'You have {{credits}} credits.',
        'fr': 'Vous avez {{credits}} crédits.',
        'es': 'Tienes {{credits}} créditos.',
        'ro': 'Ai {{credits}} credite.',
    },
    'billing-buy-credits': {
        'en': 'Buy credits',
        'fr': 'Acheter des crédits',
        'es': 'Comprar créditos',
        'ro': 'Cumpără credite',
    },
    'credits': {
        'en': 'Credits available: {{remaining}}',
        'fr': 'Crédits disponibles : {{remaining}}',
        'es': 'Créditos disponibles: {{remaining}}',
        'ro': 'Credite disponibile: {{remaining}}',
    },
    'credits-remaining': {
        'en': '{{credits}} credit(s) remaining',
        'fr': '{{credits}} crédit(s) restant(s)',
        'es': '{{credits}} crédito(s) restante(s)',
        'ro': '{{credits}} credit(e) rămase',
    },
    'credits-cost': {
        'en': 'This will use {{credits}} credit(s)',
        'fr': 'Cela utilisera {{credits}} crédit(s)',
        'es': 'Esto usará {{credits}} crédito(s)',
        'ro': 'Aceasta va folosi {{credits}} credit(e)',
    },
    'click-to-buy': {
        'en': 'Click to buy more credits',
        'fr': 'Cliquez pour acheter plus de crédits',
        'es': 'Haga clic para comprar más créditos',
        'ro': 'Faceți clic pentru a cumpăra mai multe credite',
    },
    'extra-credits': {
        'en': 'extra credits',
        'fr': 'crédits supplémentaires',
        'es': 'créditos adicionales',
        'ro': 'credite suplimentare',
    },
    'credits-label': {
        'en': 'Credits',
        'fr': 'Crédits',
        'es': 'Créditos',
        'ro': 'Credite',
    },
    'purchase-extra-credits': {
        'en': 'Purchase extra credits',
        'fr': 'Acheter des crédits supplémentaires',
        'es': 'Comprar créditos adicionales',
        'ro': 'Cumpărați credite suplimentare',
    },
    'subscribe-for-unlimited': {
        'en': 'Or subscribe for unlimited access — a subscription removes the credit limit entirely.',
        'fr': 'Ou abonnez-vous pour un accès illimité — un abonnement supprime totalement la limite de crédits.',
        'es': 'O suscríbete para acceso ilimitado — una suscripción elimina por completo el límite de créditos.',
        'ro': 'Sau abonează-te pentru acces nelimitat — un abonament elimină complet limita de credite.',
    },
    'subscribe': {
        'en': 'Subscribe',
        'fr': "S'abonner",
        'es': 'Suscribirse',
        'ro': 'Abonează-te',
    },
    'limit-reached-description': {
        'en': 'You have used all your credits. Purchase more to continue.',
        'fr': 'Vous avez utilisé tous vos crédits. Achetez-en plus pour continuer.',
        'es': 'Has utilizado todos tus créditos. Compra más para continuar.',
        'ro': 'Ați utilizat toate creditele. Cumpărați mai multe pentru a continua.',
    },
    'price-per-credit': {
        'en': '€{{price}} per credit',
        'fr': '{{price}}€ par crédit',
        'es': '€{{price}} por crédito',
        'ro': '€{{price}} per credit',
    },
    'minimum-quantity': {
        'en': 'Minimum quantity is {{min}} extra credits',
        'fr': 'La quantité minimum est de {{min}} crédits supplémentaires',
        'es': 'La cantidad mínima es de {{min}} créditos adicionales',
        'ro': 'Cantitatea minimă este de {{min}} credite suplimentare',
    },
    'cancel': {
        'en': 'Cancel',
        'fr': 'Annuler',
        'es': 'Cancelar',
        'ro': 'Anulează',
    },
    'buy-now': {
        'en': 'Buy now',
        'fr': 'Acheter maintenant',
        'es': 'Comprar ahora',
        'ro': 'Cumpără acum',
    },
    'loading': {
        'en': 'Loading...',
        'fr': 'Chargement...',
        'es': 'Cargando...',
        'ro': 'Se încarcă...',
    },
}
