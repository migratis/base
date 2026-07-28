// Resolves the legal PDFs (terms of sale, privacy policy) for the language the
// visitor is reading the site in. The documents themselves are built from
// docs/legal/*.html — see docs/legal/build.sh; never edit the PDFs by hand.
import cguvEn from "../../documents/cguv_en.pdf";
import cguvFr from "../../documents/cguv_fr.pdf";
import cguvEs from "../../documents/cguv_es.pdf";
import cguvRo from "../../documents/cguv_ro.pdf";
import rgpdEn from "../../documents/rgpd_en.pdf";
import rgpdFr from "../../documents/rgpd_fr.pdf";
import rgpdEs from "../../documents/rgpd_es.pdf";
import rgpdRo from "../../documents/rgpd_ro.pdf";

const CGUV = { en: cguvEn, fr: cguvFr, es: cguvEs, ro: cguvRo };
const RGPD = { en: rgpdEn, fr: rgpdFr, es: rgpdEs, ro: rgpdRo };

// i18next hands out tags like 'fr-FR'; anything we do not publish falls back to
// English rather than to a broken link.
const pick = (documents, language) => documents[(language || '').substring(0, 2)] || documents.en;

export const cguvDocument = (language) => pick(CGUV, language);
export const rgpdDocument = (language) => pick(RGPD, language);
