import type { User } from '../types';

interface Props {
  user: User;
}

function UserCard({ user }: Props) {
  return (
    <div className="user-side">
      <h4>{user.display_name}</h4>
      <div className="adds">
        {user.adds.map(p => (
           <div className={p.signal ? "has-signal" : ""}>
             + {p.name} {p.signal && <span className="alert">⚠️</span>}
           </div>
        ))}
      </div>
      <div className="drops">
        {user.drops.map(p => (
           <div className={p.signal ? "has-signal" : ""}>
             - {p.name} {p.signal && <span className="alert">⚠️</span>}
           </div>
        ))}
      </div>
    </div>
  );
}

export default UserCard;