export const API_SERVER = window.location.host.match("127.0.0.1")?'http://127.0.0.1:8004/backend/api/':(window.location.href.match('dev')?'https://dev.migratis.com/backend/api/':'https://www.migratis.com/backend/api/');
export const STRIPE_API_KEY = window.location.href.match('dev')?"pk_test_51RqyyyPGwtp57pxfqRYymcjXFpsAVeOZRPUnouiJNbU8LpYVGFt2PpGMBsGEnJ42PpF8PZORFQEwrcNei546v0Po00OoqsiFAs":"pk_live_51M9oRxAXmadDuP9DSDzNetvVNXyzw4VEcbSZOvRC3LgXRfWZIATP8HvGSw5E8a0EPqSQTLJjPO3nqzFnoqjAusmH00XzZvbQgn";
export const ITEMS_PER_PAGE = 6;
export const COLOR_LINK = '#d9775798'
export const SUPPORT = false;
export const CONTACT = false;
export const SUBSCRIPTION = false;
export const USER = false;
export const COOKIE = false;
export const INSTALLER = true;



