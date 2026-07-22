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
    'hero-title': {
        'en': 'Build Apps with AI',
        'fr': "Créez des Applications avec l'IA",
        'es': 'Cree Aplicaciones con IA',
        'ro': 'Construiți Aplicații cu IA',
    },
    'hero-subtitle': {
        'en': 'Design, prototype, and generate full-stack applications powered by AI',
        'fr': "Concevez, prototypez et générez des applications full-stack alimentées par l'IA",
        'es': 'Diseñe, prototipe y genere aplicaciones full-stack impulsadas por IA',
        'ro': 'Proiectați, prototipați și generați aplicații full-stack alimentate de IA',
    },
    'get-started': {
        'en': 'Get Started',
        'fr': 'Commencer',
        'es': 'Comenzar',
        'ro': 'Începeți',
    },
    'ch1-title': {
        'en': 'AI-Powered Schema Design',
        'fr': "Conception de Schéma Alimentée par l'IA",
        'es': 'Diseño de Esquema Impulsado por IA',
        'ro': 'Proiectare Schemă Alimentată de IA',
    },
    'ch1-desc': {
        'en': 'Describe your application in plain language and let our AI generate the complete data model with entities, fields, relationships, and validation rules.',
        'fr': 'Décrivez votre application en langage naturel et laissez notre IA générer le modèle de données complet avec entités, champs, relations et règles de validation.',
        'es': 'Describa su aplicación en lenguaje natural y deje que nuestra IA genere el modelo de datos completo con entidades, campos, relaciones y reglas de validación.',
        'ro': 'Descrieți aplicația în limbaj natural și lăsați IA noastră să genereze modelul de date complet cu entități, câmpuri, relații și reguli de validare.',
    },
    'ch1-f1': {
        'en': 'Natural language application descriptions',
        'fr': "Descriptions d'application en langage naturel",
        'es': 'Descripciones de aplicación en lenguaje natural',
        'ro': 'Descrieri de aplicație în limbaj natural',
    },
    'ch1-f2': {
        'en': 'Automatic entity and field generation',
        'fr': "Génération automatique d'entités et de champs",
        'es': 'Generación automática de entidades y campos',
        'ro': 'Generare automată de entități și câmpuri',
    },
    'ch1-f3': {
        'en': 'Smart relationship detection',
        'fr': 'Détection intelligente des relations',
        'es': 'Detección inteligente de relaciones',
        'ro': 'Detectare inteligentă a relațiilor',
    },
    'ch1-f4': {
        'en': 'AI-guided validation rules',
        'fr': "Règles de validation guidées par l'IA",
        'es': 'Reglas de validación guiadas por IA',
        'ro': 'Reguli de validare ghidate de IA',
    },
    'ch2-title': {
        'en': 'Interactive Sandbox Testing',
        'fr': 'Test Bac à Sable Interactif',
        'es': 'Pruebas en Sandbox Interactivo',
        'ro': 'Testare Sandbox Interactiv',
    },
    'ch2-desc': {
        'en': 'Test your data model in a live sandbox environment before generating any code. Create, edit, and delete records to verify your schema works exactly as intended.',
        'fr': 'Testez votre modèle de données dans un environnement bac à sable avant de générer du code. Créez, modifiez et supprimez des enregistrements pour vérifier que votre schéma fonctionne comme prévu.',
        'es': 'Pruebe su modelo de datos en un entorno sandbox antes de generar código. Cree, edite y elimine registros para verificar que su esquema funciona como se espera.',
        'ro': 'Testați modelul de date într-un mediu sandbox înainte de a genera cod. Creați, editați și ștergeți înregistrări pentru a verifica că schema funcționează conform așteptărilor.',
    },
    'ch2-f1': {
        'en': 'Real-time data model testing',
        'fr': 'Test de modèle de données en temps réel',
        'es': 'Pruebas de modelo de datos en tiempo real',
        'ro': 'Testare model de date în timp real',
    },
    'ch2-f2': {
        'en': 'Search, filter, and sort records',
        'fr': 'Rechercher, filtrer et trier les enregistrements',
        'es': 'Buscar, filtrar y ordenar registros',
        'ro': 'Căutați, filtrați și sortați înregistrări',
    },
    'ch2-f3': {
        'en': 'Multiple display modes (table, cards, kanban)',
        'fr': "Modes d'affichage multiples (tableau, cartes, kanban)",
        'es': 'Múltiples modos de visualización (tabla, tarjetas, kanban)',
        'ro': 'Moduri multiple de afișare (tabel, carduri, kanban)',
    },
    'ch2-f4': {
        'en': 'AI-powered sandbox configuration',
        'fr': "Configuration de bac à sable alimentée par l'IA",
        'es': 'Configuración de sandbox impulsada por IA',
        'ro': 'Configurare sandbox alimentată de IA',
    },
    'ch3-title': {
        'en': 'One-Click Code Generation',
        'fr': 'Génération de Code en un Clic',
        'es': 'Generación de Código con un Clic',
        'ro': 'Generare Cod cu un Clic',
    },
    'ch3-desc': {
        'en': 'Generate production-ready Django backend and React frontend code from your validated schema. Everything you need to deploy your application.',
        'fr': 'Générez du code backend Django et frontend React prêt pour la production à partir de votre schéma validé. Tout ce dont vous avez besoin pour déployer votre application.',
        'es': 'Genere código backend Django y frontend React listo para producción desde su esquema validado. Todo lo que necesita para desplegar su aplicación.',
        'ro': 'Generați cod backend Django și frontend React gata de producție din schema validată. Tot ce aveți nevoie pentru a implementa aplicația.',
    },
    'ch3-f1': {
        'en': 'Django models and APIs',
        'fr': 'Modèles et API Django',
        'es': 'Modelos y APIs Django',
        'ro': 'Modele și API-uri Django',
    },
    'ch3-f2': {
        'en': 'React components and forms',
        'fr': 'Composants et formulaires React',
        'es': 'Componentes y formularios React',
        'ro': 'Componente și formulare React',
    },
    'ch3-f3': {
        'en': 'Admin interface configuration',
        'fr': "Configuration de l'interface d'administration",
        'es': 'Configuración de interfaz de administración',
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
        'fr': 'Dépôt Public "base"',
        'es': 'Repositorio Público "base"',
        'ro': 'Depozit Public "base"',
    },
    'ch4-desc': {
        'en': 'Migratis provides a public GitHub repository called "base" from which you can install any application generated by the platform. Your apps are ready to deploy in minutes.',
        'fr': 'Migratis fournit un dépôt GitHub public appelé "base" depuis lequel vous pouvez installer toute application générée par la plateforme. Vos applications sont prêtes à être déployées en quelques minutes.',
        'es': 'Migratis proporciona un repositorio público de GitHub llamado "base" desde el cual puede instalar cualquier aplicación generada por la plataforma. Sus aplicaciones están listas para desplegar en minutos.',
        'ro': 'Migratis oferă un depozit public GitHub numit "base" din care puteți instala orice aplicație generată de platformă. Aplicațiile dvs. sunt gata de implementare în câteva minute.',
    },
    'ch4-f1': {
        'en': 'Pre-configured Django project structure',
        'fr': 'Structure de projet Django pré-configurée',
        'es': 'Estructura de proyecto Django preconfigurada',
        'ro': 'Structură de proiect Django pre-configurată',
    },
    'ch4-f2': {
        'en': 'Ready-to-install application modules',
        'fr': "Modules d'application prêts à installer",
        'es': 'Módulos de aplicación listos para instalar',
        'ro': 'Module de aplicație gata de instalare',
    },
    'ch4-f3': {
        'en': 'One-command deployment setup',
        'fr': 'Configuration de déploiement en une commande',
        'es': 'Configuración de despliegue con un comando',
        'ro': 'Configurare de implementare cu o comandă',
    },
    'ch4-f4': {
        'en': 'Shared infrastructure and dependencies',
        'fr': 'Infrastructure et dépendances partagées',
        'es': 'Infraestructura y dependencias compartidas',
        'ro': 'Infrastructură și dependențe partajate',
    },
    'ch5-title': {
        'en': 'Multi-Language Support',
        'fr': 'Support Multi-Langues',
        'es': 'Soporte Multi-Idioma',
        'ro': 'Suport Multi-Limbă',
    },
    'ch5-desc': {
        'en': 'Build applications that support multiple languages out of the box. Our AI generates translations for all your entities and fields.',
        'fr': 'Créez des applications qui supportent plusieurs langues dès le départ. Notre IA génère des traductions pour toutes vos entités et champs.',
        'es': 'Cree aplicaciones que soporten múltiples idiomas desde el inicio. Nuestra IA genera traducciones para todas sus entidades y campos.',
        'ro': 'Construiți aplicații care suportă mai multe limbi de la început. IA noastră generează traduceri pentru toate entitățile și câmpurile dvs.',
    },
    'ch5-f1': {
        'en': 'Built-in i18n support',
        'fr': 'Support i18n intégré',
        'es': 'Soporte i18n integrado',
        'ro': 'Suport i18n integrat',
    },
    'ch5-f2': {
        'en': 'AI-generated translations',
        'fr': "Traductions générées par l'IA",
        'es': 'Traducciones generadas por IA',
        'ro': 'Traduceri generate de IA',
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
        'es': 'Fácil gestión de traducciones',
        'ro': 'Gestionare ușoară a traducerilor',
    },
    'ch6-title': {
        'en': 'Ready-Made Modules',
        'fr': "Modules Prêts à l'Emploi",
        'es': 'Módulos Listos para Usar',
        'ro': 'Module Gata Făcute',
    },
    'ch6-desc': {
        'en': 'Accelerate development with pre-built modules for authentication, subscriptions, internationalization, support tickets, and cookie consent.',
        'fr': "Accélérez le développement avec des modules pré-construits pour l'authentification, les abonnements, l'internationalisation, les tickets de support et le consentement aux cookies.",
        'es': 'Acelere el desarrollo con módulos preconstruidos para autenticación, suscripciones, internacionalización, tickets de soporte y consentimiento de cookies.',
        'ro': 'Accelerați dezvoltarea cu module pre-construite pentru autentificare, abonamente, internaționalizare, tickete de suport și consimțământ cookie.',
    },
    'ch6-f1': {
        'en': 'User authentication & profiles',
        'fr': 'Authentification et profils utilisateurs',
        'es': 'Autenticación y perfiles de usuario',
        'ro': 'Autentificare și profiluri utilizator',
    },
    'ch6-f2': {
        'en': 'Stripe subscription billing',
        'fr': 'Facturation par abonnement Stripe',
        'es': 'Facturación por suscripción Stripe',
        'ro': 'Facturare prin abonament Stripe',
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
        'ro': 'Sistem de suport pentru clienți',
    },
    'ch7-title': {
        'en': 'Security & Best Practices',
        'fr': 'Sécurité et Meilleures Pratiques',
        'es': 'Seguridad y Mejores Prácticas',
        'ro': 'Securitate și Cele Mai Bune Practici',
    },
    'ch7-desc': {
        'en': 'Generated code follows Django and React best practices with proper security measures, validation, and error handling built-in.',
        'fr': 'Le code généré suit les meilleures pratiques Django et React avec des mesures de sécurité appropriées, la validation et la gestion des erreurs intégrées.',
        'es': 'El código generado sigue las mejores prácticas de Django y React con medidas de seguridad adecuadas, validación y manejo de errores integrados.',
        'ro': 'Codul generat urmează cele mai bune practici Django și React cu măsuri de securitate adecvate, validare și gestionare erori integrate.',
    },
    'ch7-f1': {
        'en': 'CSRF and XSS protection',
        'fr': 'Protection CSRF et XSS',
        'es': 'Protección CSRF y XSS',
        'ro': 'Protecție CSRF și XSS',
    },
    'ch7-f2': {
        'en': 'Input validation included',
        'fr': 'Validation des entrées incluse',
        'es': 'Validación de entrada incluida',
        'ro': 'Validare input inclusă',
    },
    'ch7-f3': {
        'en': 'Role-based access control',
        'fr': "Contrôle d'accès basé sur les rôles",
        'es': 'Control de acceso basado en roles',
        'ro': 'Control acces bazat pe roluri',
    },
    'ch7-f4': {
        'en': 'Clean, documented code',
        'fr': 'Code propre et documenté',
        'es': 'Código limpio y documentado',
        'ro': 'Cod curat și documentat',
    },
    'ch8-title': {
        'en': 'Workflow Automation',
        'fr': 'Automatisation des Workflows',
        'es': 'Automatización de Flujos de Trabajo',
        'ro': 'Automatizare Fluxuri de Lucru',
    },
    'ch8-desc': {
        'en': 'Define automated workflows that trigger actions based on events. Create, update, compute, and export data automatically with AI-guided logic.',
        'fr': "Définissez des workflows automatisés qui déclenchent des actions basées sur des événements. Créez, mettez à jour, calculez et exportez des données automatiquement avec une logique guidée par l'IA.",
        'es': 'Defina flujos de trabajo automatizados que desencadenen acciones basadas en eventos. Cree, actualice, calcule y exporte datos automáticamente con lógica guiada por IA.',
        'ro': 'Definiți fluxuri de lucru automate care declanșează acțiuni bazate pe evenimente. Creați, actualizați, calculați și exportați date automat cu logică ghidată de IA.',
    },
    'ch8-f1': {
        'en': 'Event-driven automation',
        'fr': 'Automatisation pilotée par les événements',
        'es': 'Automatización basada en eventos',
        'ro': 'Automatizare bazată pe evenimente',
    },
    'ch8-f2': {
        'en': 'AI-assisted workflow design',
        'fr': "Conception de workflow assistée par l'IA",
        'es': 'Diseño de flujo de trabajo asistido por IA',
        'ro': 'Proiectare flux de lucru asistat de IA',
    },
    'ch8-f3': {
        'en': 'Visual workflow builder',
        'fr': 'Constructeur visuel de workflow',
        'es': 'Constructor visual de flujo de trabajo',
        'ro': 'Constructor vizual de flux de lucru',
    },
    'ch8-f4': {
        'en': 'Scheduled and triggered actions',
        'fr': 'Actions planifiées et déclenchées',
        'es': 'Acciones programadas y desencadenadas',
        'ro': 'Acțiuni programate și declanșate',
    },
    'cta-title': {
        'en': 'Ready to Build Your First App?',
        'fr': 'Prêt à Construire Votre Première App ?',
        'es': '¿Listo para Construir su Primera App?',
        'ro': 'Gata să Construiți Prima Aplicație?',
    },
    'cta-desc': {
        'en': 'Start designing your application with AI-powered tools today.',
        'fr': "Commencez à concevoir votre application avec des outils alimentés par l'IA dès aujourd'hui.",
        'es': 'Comience a diseñar su aplicación con herramientas impulsadas por IA hoy.',
        'ro': 'Începeți să proiectați aplicația cu instrumente alimentate de IA astăzi.',
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
        'en': 'Seeded data was not touched. To load the translation keys added by this version, run:',
        'fr': "Les données initiales n'ont pas été modifiées. Pour charger les clés de traduction ajoutées par cette version, exécutez :",
        'es': 'Los datos iniciales no se modificaron. Para cargar las claves de traducción añadidas por esta versión, ejecute:',
        'ro': 'Datele inițiale nu au fost modificate. Pentru a încărca cheile de traducere adăugate de această versiune, rulați:',
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
        'fr': "Construire des Apps avec l'IA",
        'es': 'Crear Apps con IA',
        'ro': 'Construiește Aplicații cu AI',
    },
    'hero-subtitle': {
        'en': 'Design, prototype, and generate full-stack applications powered by AI',
        'fr': "Concevez, prototypisez et générez des applications full-stack alimentées par l'IA",
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
        'fr': "Conception de schéma alimentée par l'IA",
        'es': 'Diseño de esquema con IA',
        'ro': 'Proiectare schemă cu AI',
    },
    'ch1-desc': {
        'en': 'Describe your application in plain language and let our AI generate the complete data model with entities, fields, relationships, and validation rules.',
        'fr': 'Décrivez votre application en langage naturel et laissez notre IA générer le modèle de données complet avec entités, champs, relations et règles de validation.',
        'es': 'Describe tu aplicación en lenguaje natural y deja que nuestra IA genere el modelo de datos completo con entidades, campos, relaciones y reglas de validación.',
        'ro': 'Descrie aplicația ta în limbaj natural și lasă AI-ul nostru să genereze modelul de date complet cu entități, câmpuri, relații și reguli de validare.',
    },
    'ch1-f1': {
        'en': 'Natural language application descriptions',
        'fr': "Descriptions d'application en langage naturel",
        'es': 'Descripciones de aplicación en lenguaje natural',
        'ro': 'Descrieri de aplicații în limbaj natural',
    },
    'ch1-f2': {
        'en': 'Automatic entity and field generation',
        'fr': "Génération automatique d'entités et de champs",
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
        'en': 'AI-guided validation rules',
        'fr': "Règles de validation guidées par l'IA",
        'es': 'Reglas de validación guiadas por IA',
        'ro': 'Reguli de validare ghidate de AI',
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
        'en': 'Multiple display modes (table, cards, kanban)',
        'fr': "Modes d'affichage multiples (tableau, cartes, kanban)",
        'es': 'Múltiples modos de visualización (tabla, tarjetas, kanban)',
        'ro': 'Moduri de afișare multiple (tabel, carduri, kanban)',
    },
    'ch2-f4': {
        'en': 'AI-powered sandbox configuration',
        'fr': "Configuration du bac à sable alimentée par l'IA",
        'es': 'Configuración de sandbox impulsada por IA',
        'ro': 'Configurare sandbox alimentată de AI',
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
        'fr': "Configuration de l'interface d'administration",
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
        'fr': "Modules d'application prêts à installer",
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
        'en': 'Shared infrastructure and dependencies',
        'fr': 'Infrastructure et dépendances partagées',
        'es': 'Infraestructura y dependencias compartidas',
        'ro': 'Infrastructură și dependențe partajate',
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
        'fr': "Traductions générées par l'IA",
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
        'fr': "Modules prêts à l'emploi",
        'es': 'Módulos listos para usar',
        'ro': 'Module gata de utilizare',
    },
    'ch6-desc': {
        'en': 'Accelerate development with pre-built modules for authentication, subscriptions, internationalization, support tickets, and cookie consent.',
        'fr': "Accélérez le développement avec des modules pré-construits pour l'authentification, les abonnements, l'internationalisation, les tickets de support et le consentement aux cookies.",
        'es': 'Acelera el desarrollo con módulos preconstruidos para autenticación, suscripciones, internacionalización, tickets de soporte y consentimiento de cookies.',
        'ro': 'Accelerează dezvoltarea cu module pre-construite pentru autentificare, abonamente, internaționalizare, tichete de suport și consimțământ cookie.',
    },
    'ch6-f1': {
        'en': 'User authentication & profiles',
        'fr': 'Authentification et profils utilisateur',
        'es': 'Autenticación y perfiles de usuario',
        'ro': 'Autentificare și profiluri utilizator',
    },
    'ch6-f2': {
        'en': 'Stripe subscription billing',
        'fr': 'Facturation des abonnements Stripe',
        'es': 'Facturación de suscripciones Stripe',
        'ro': 'Facturare abonamente Stripe',
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
        'fr': "Votre application suit les bonnes pratiques de sécurité avec une protection intégrée contre les vulnérabilités courantes, un contrôle d'accès basé sur les rôles et des mises à jour de sécurité régulières.",
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
        'fr': "Contrôle d'accès basé sur les rôles",
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
        'fr': "Définissez des flux de travail automatisés qui déclenchent des actions basées sur des événements. Créez, mettez à jour, calculez et exportez des données automatiquement avec une logique guidée par l'IA.",
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
        'fr': "Conception de flux de travail assistée par l'IA",
        'es': 'Diseño de flujo de trabajo asistido por IA',
        'ro': 'Proiectare flux de lucru asistată de AI',
    },
    'ch8-f3': {
        'en': 'Visual workflow builder',
        'fr': 'Constructeur de flux de travail visuel',
        'es': 'Constructor visual de flujos de trabajo',
        'ro': 'Constructor vizual fluxuri de lucru',
    },
    'ch8-f4': {
        'en': 'Scheduled and triggered actions',
        'fr': 'Actions planifiées et déclenchées',
        'es': 'Acciones programadas y disparadas',
        'ro': 'Acțiuni programate și declanșate',
    },
    'cta-title': {
        'en': 'Ready to Build Your First App?',
        'fr': 'Prêt à construire votre première application ?',
        'es': '¿Listo para construir tu primera aplicación?',
        'ro': 'Gata să construiești prima ta aplicație?',
    },
    'cta-desc': {
        'en': 'Start designing your application with AI-powered tools today.',
        'fr': "Commencez à concevoir votre application avec des outils alimentés par l'IA dès aujourd'hui.",
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
    'billing-intro': {
        'en': 'Subscribe for ongoing access, or buy AI credits as you need them — both power maintaining your app and deploying new versions to your base.',
        'fr': 'Abonnez-vous pour un accès continu, ou achetez des crédits IA selon vos besoins — les deux permettent de maintenir votre application et de déployer de nouvelles versions vers votre base.',
        'es': 'Suscríbete para acceso continuo, o compra créditos de IA cuando los necesites — ambos permiten mantener tu aplicación y desplegar nuevas versiones a tu base.',
        'ro': 'Abonează-te pentru acces continuu sau cumpără credite AI după nevoie — ambele permit întreținerea aplicației și implementarea de noi versiuni în baza ta.',
    },
    'billing-subscription-title': {
        'en': 'Subscription',
        'fr': 'Abonnement',
        'es': 'Suscripción',
        'ro': 'Abonament',
    },
    'billing-credits-title': {
        'en': 'AI credits',
        'fr': 'Crédits IA',
        'es': 'Créditos de IA',
        'ro': 'Credite AI',
    },
    'billing-credits-balance': {
        'en': 'You have {{credits}} AI credits.',
        'fr': 'Vous avez {{credits}} crédits IA.',
        'es': 'Tienes {{credits}} créditos de IA.',
        'ro': 'Ai {{credits}} credite AI.',
    },
    'billing-credits-unlimited': {
        'en': 'Your subscription includes unlimited AI — no credits needed.',
        'fr': 'Votre abonnement inclut une IA illimitée — aucun crédit nécessaire.',
        'es': 'Tu suscripción incluye IA ilimitada — no se necesitan créditos.',
        'ro': 'Abonamentul tău include AI nelimitat — nu sunt necesare credite.',
    },
    'billing-buy-credits': {
        'en': 'Buy credits',
        'fr': 'Acheter des crédits',
        'es': 'Comprar créditos',
        'ro': 'Cumpără credite',
    },
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
    'confirm-link-in-email': {
        'en': 'Confirmation link sent to your email',
        'fr': 'Lien de confirmation envoyé à votre email',
        'es': 'Enlace de confirmación enviado a tu correo',
        'ro': 'Link de confirmare trimis pe email',
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
}

TRANSLATIONS['register'] = {
    'register': {
        'en': 'Register',
        'fr': "S'inscrire",
        'es': 'Registrarse',
        'ro': 'Înregistrare',
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
    'credits': {
        'en': 'Credits',
        'fr': 'Crédits',
        'es': 'Créditos',
        'ro': 'Credite',
    },
}

# ── credits (migratis.credits) ─────────────────────────────────────────────
# De-AI'd credit widget / purchase-modal copy. The credits FE module resolves
# from `credits` + `billing` only.
TRANSLATIONS['credits'] = {
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
