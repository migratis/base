import { useTranslation } from 'react-i18next';
import { PageShell } from '../../common/components/PageShell';
import { UserForm } from './UserForm';

const Register = (props) => {
  const { t } = useTranslation('register');
  const profile = {
    first_name: "",
    last_name: "",
    birthdate: new Date(),
    address: "",
    zipcode: "",
    city: "",      
    country: null,   
    professional: false,                               
    company: "",
    taxnumber: ""				  
  }

  return (
    <PageShell title={ t('register') } width="form">
      <UserForm profile={profile} register={true}/>
    </PageShell>
  );

};

export default Register;
