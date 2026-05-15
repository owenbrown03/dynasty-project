import './Home.css';
import { useNavigate } from 'react-router';
import { useUsernameLookup } from '../../hooks/usernameHandler';
import UsernameInput from './UsernameInput';

const Home = () => {
  const navigate = useNavigate();
  const { loading, handleUserSubmit } = useUsernameLookup();

  const handleSubmit = async (username: string) => {
    await handleUserSubmit(username);
    if (username) {
      navigate(`/${encodeURIComponent(username)}/rosters`);
    }
  };

  return (
    <>
      <UsernameInput setUsername={handleSubmit} />
      {loading && <p>Fetching data...</p>}
    </>
  );
};

export default Home;
