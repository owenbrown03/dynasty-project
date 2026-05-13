import './Home.css';
import UsernameInput from './UsernameInput';

const Home = ({ onSubmit, loading }) => {
  return (
    <>
      <UsernameInput setUsername={onSubmit} />
      {loading && <p>Fetching data...</p>}
    </>
  );
};

export default Home;