import './UserCard.css';
import type { UserMovements } from '../../types';

interface Props {
  user: UserMovements;
}

export function UserCard({ user }: Props) {
  return (
    <div className="user-card">
      <header className="user-header">{user.display_name}</header>
      <div className="adds">
          {user.adds.map((p, index) => (
             <div key={`add-${index}`}className={p.signal ? "has-signal movement-row" : "movement-row"}>
             <span className="movement-prefix">+</span>{p.name} {p.signal ? <span className="sell">{p.signal}</span> : ""}
           </div>
        ))}
      </div>
      <div className="drops">
          {user.drops.map((p, index) => (
             <div key={`drop-${index}`} className={p.signal ? "has-signal movement-row" : "movement-row"}>
             <span className="movement-prefix">-</span>{p.name} {p.signal ? <span className="buy">{p.signal}</span> : ""}
           </div>
        ))}
      </div>
    </div>
  );
}
