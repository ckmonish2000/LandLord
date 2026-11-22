import { useMemo, useState } from "react";
import { formatPhone } from "../format";
import type { Account, Group } from "../types";
import { accountLabel } from "./AccountRail";
import Avatar from "./Avatar";
import { BackIcon, RefreshIcon, SearchIcon } from "./Icons";

interface Props {
  account: Account | null;
  groups: Group[] | null;
  loading: boolean;
  error: string | null;
  selectedJid: string | null;
  onSelect: (g: Group) => void;
  onRefresh: () => void;
  onLink: () => void;
  /** Group JIDs already added as properties (tagged "Added"). */
  addedJids?: Set<string>;
  /** When set, the header shows "Choose a group" with a back button. */
  onBack?: () => void;
}

/** Middle column: the selected account's groups, with search. */
export default function GroupList({
  account,
  groups,
  loading,
  error,
  selectedJid,
  onSelect,
  onRefresh,
  onLink,
  addedJids,
  onBack,
}: Props) {
  const [query, setQuery] = useState("");

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = groups ?? [];
    const sorted = [...list].sort((a, b) => a.name.localeCompare(b.name));
    return q ? sorted.filter((g) => g.name.toLowerCase().includes(q) || g.topic?.toLowerCase().includes(q)) : sorted;
  }, [groups, query]);

  return (
    <section className="list-panel">
      <header className="list-header">
        {onBack && (
          <button className="icon-btn" onClick={onBack} title="Back to properties">
            <BackIcon />
          </button>
        )}
        <div className="list-title">
          <h2>{onBack ? "Choose a group" : account ? accountLabel(account) : "Landlord"}</h2>
          {onBack ? (
            <span className="muted small">Each group is one property</span>
          ) : (
            account?.phone && <span className="muted small">{formatPhone(account.phone)}</span>
          )}
        </div>
        {account && (
          <button className="icon-btn" onClick={onRefresh} title="Reload groups" disabled={loading}>
            <RefreshIcon />
          </button>
        )}
      </header>

      {account && (
        <div className="search">
          <SearchIcon />
          <input placeholder="Search groups" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
      )}

      {groups && groups.length > 0 && (
        <div className="list-meta muted small">
          {query ? `${visible.length} of ${groups.length} groups` : `${groups.length} groups`}
        </div>
      )}

      <div className="list-body">
        {!account && !loading && (
          <div className="empty">
            <p>No WhatsApp account linked yet.</p>
            <button className="btn-primary" onClick={onLink}>Link WhatsApp</button>
          </div>
        )}

        {account && account.status !== "connected" && (
          <div className="empty">
            <p>This account was logged out from the phone.</p>
            <button className="btn-primary" onClick={onLink}>Link again</button>
          </div>
        )}

        {loading && (
          <div className="empty muted">{account ? "Loading groups… this can take a moment." : "Loading…"}</div>
        )}

        {account?.status === "connected" && !loading && error && (
          <div className="empty">
            <p className="form-error">{error}</p>
            <button className="btn-secondary" onClick={onRefresh}>Try again</button>
          </div>
        )}

        {!loading && !error && groups && visible.length === 0 && (
          <div className="empty muted">{query ? "No groups match your search." : "This account isn't in any groups."}</div>
        )}

        {!loading &&
          visible.map((g) => (
            <button
              key={g.jid}
              className={`list-item ${g.jid === selectedJid ? "selected" : ""}`}
              onClick={() => onSelect(g)}
            >
              <Avatar name={g.name} src={g.picture_url} kind="group" size={49} />
              <div className="item-text">
                <div className="item-row">
                  <span className="item-title">{g.name || "Unnamed group"}</span>
                  <span className="muted small nowrap">{g.participant_count}</span>
                </div>
                <div className="item-row">
                  <span className="item-sub muted">{g.topic || `${g.participant_count} members`}</span>
                  <span className="tags">
                    {addedJids?.has(g.jid) && <span className="tag accent">Added</span>}
                    {g.is_community && <span className="tag">Community</span>}
                    {g.is_announce && <span className="tag">Admins only</span>}
                  </span>
                </div>
              </div>
            </button>
          ))}
      </div>
    </section>
  );
}
