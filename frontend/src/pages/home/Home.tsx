import './Home.css';
import UsernameInput from './UsernameInput';

const Home = ({ onSubmit, loading }) => (
  <>
    <UsernameInput setUsername={onSubmit} />
    {loading && <p>Fetching data...</p>}
  </>
);

export default Home;