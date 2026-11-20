import { formatPhone } from "../format";
import type { Account, User } from "../types";
import Avatar from "./Avatar";
import { LogoutIcon, PlusIcon } from "./Icons";

interface Props {
  user: User;
  accounts: Account[] | null;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onLink: () => void;
  onLogout: () => void;
}

export function accountLabel(a: Account): string {
  return a.push_name || a.business_name || formatPhone(a.phone) || "WhatsApp account";
}

/** Narrow far-left column: one avatar per linked WhatsApp account. */
export default function AccountRail({ user, accounts, selectedId, onSelect, onLink, onLogout }: Props) {
  return (
    <nav className="rail" aria-label="WhatsApp accounts">
      <div className="rail-accounts">
        {accounts?.map((a) => {
          const label = accountLabel(a);
          const connected = a.status === "connected";
          return (
            <button
              key={a.id}
              className={`rail-account ${a.id === selectedId ? "selected" : ""}`}
              onClick={() => onSelect(a.id)}
              title={`${label}${a.phone ? ` · ${formatPhone(a.phone)}` : ""} · ${connected ? "connected" : "logged out"}`}
              aria-pressed={a.id === selectedId}
            >
              <Avatar name={label} size={40} />
              <span className={`status-dot ${connected ? "online" : "offline"}`} />
            </button>
          );
        })}
        {accounts && accounts.length === 0 && (
          <button className="rail-icon accent" onClick={onLink} title="Link a WhatsApp account">
            <PlusIcon />
          </button>
        )}
      </div>

      <div className="rail-bottom">
        <div title={`${user.name} · ${user.email}`}>
          <Avatar name={user.name} size={34} />
        </div>
        <button className="rail-icon" onClick={onLogout} title="Log out">
          <LogoutIcon size={20} />
        </button>
      </div>
    </nav>
  );
}
