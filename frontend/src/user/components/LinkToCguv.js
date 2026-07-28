import { useTranslation } from 'react-i18next';
import { cguvDocument } from "../../common/tools/legalDocuments";
import { IoDownloadOutline as DownloadOutline} from 'react-icons/io5';
import { COLOR_LINK } from '../../settings';

export const LinkToCguv = () => {
  const { t, i18n } = useTranslation('register');
  return (
    <>
      { t('link-to-cgu')  }&nbsp;
      <a target="_blank" rel="noreferrer" href={cguvDocument(i18n.language)} className="link btn btn-white">
        <DownloadOutline color={COLOR_LINK} title={t('download-cgu')} height="25px" width="25px"/>
      </a>
    </>
  );
};