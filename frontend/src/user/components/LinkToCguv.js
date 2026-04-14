import { useTranslation } from 'react-i18next';
import cguv from "../../documents/cguv.txt";
import { IoDownloadOutline as DownloadOutline} from 'react-icons/io5';
import { COLOR_LINK } from '../../settings';

export const LinkToCguv = () => {
  const { t } = useTranslation('register');
  return (
    <>  
      { t('link-to-cgu')  }&nbsp;
      <a target="_blank" rel="noreferrer" href={cguv} className="link btn btn-white">
        <DownloadOutline color={COLOR_LINK} title={t('download-cgu')} height="25px" width="25px"/>
      </a>
    </>
  );
};