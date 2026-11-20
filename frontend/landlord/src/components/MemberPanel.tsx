import { useMemo, useState } from "react";
import { formatPhone } from "../format";
import type { Group, Member } from "../types";
import Avatar from "./Avatar";
import { GroupIcon, SearchIcon } from "./Icons";

interface Props {
  group: Group | null;
  members: Member[] | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

/** WhatsApp style: saved contact name as title; otherwise the number, with ~push name below. */
function memberTitle(m: Member): string {
  return m.saved_name || formatPhone(m.phone) || m.push_name || "Hidden number";
}

function memberSubtitle(m: Member): string | null {
  if (m.saved_name) return m.push_name ? `~ ${m.push_name}` : formatPhone(m.phone);
  if (m.phone && m.push_name) return `~ ${m.push_name}`;
  return m.business_name;
}

const rank = (m: Member) => (m.is_super_admin ? 0 : m.is_admin ? 1 : 2);

/** Right column: members of the selected group. */
export default function MemberPanel({ group, members, loading, error, onRetry }: Props) {
  const [query, setQuery] = useState("");

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const sorted = [...(members ?? [])].sort(
      (a, b) => rank(a) - rank(b) || memberTitle(a).localeCompare(memberTitle(b)),
    );
    if (!q) return sorted;
    return sorted.filter((m) =>
      [m.saved_name, m.push_name, m.business_name, m.phone].some((v) => v?.toLowerCase().includes(q)),
    );
  }, [members, query]);

  if (!group) {
    return (
      <section className="detail-panel detail-empty">
        <div className="detail-empty-icon"><GroupIcon size={56} /></div>
        <h2>Select a group</h2>
        <p className="muted">Pick a group on the left to see its members.</p>
      </section>
    );
  }

  return (
    <section className="detail-panel">
      <header className="detail-header">
        <Avatar name={group.name} src={group.picture_url} kind="group" size={42} />
        <div className="detail-title">
          <h2>{group.name || "Unnamed group"}</h2>
          <span className="muted small">
            {group.participant_count} members
            {group.topic ? ` · ${group.topic}` : ""}
          </span>
        </div>
      </header>

      <div className="detail-body">
        <div className="search">
          <SearchIcon />
          <input placeholder="Search members" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>

        {loading && <div className="empty muted">Loading members…</div>}

        {!loading && error && (
          <div className="empty">
            <p className="form-error">{error}</p>
            <button className="btn-secondary" onClick={onRetry}>Try again</button>
          </div>
        )}

        {!loading && !error && members && (
          <>
            <div className="list-meta muted small">
              {query ? `${visible.length} of ${members.length} members` : `${members.length} members`}
            </div>
            <ul className="member-list">
              {visible.map((m) => {
                const title = memberTitle(m);
                const sub = memberSubtitle(m);
                return (
                  <li key={m.jid} className="member">
                    <Avatar name={m.saved_name || m.push_name || m.phone || "?"} src={m.picture_url} size={44} />
                    <div className="item-text">
                      <div className="item-row">
                        <span className="item-title">{title}</span>
                        {m.is_super_admin ? (
                          <span className="tag accent">Owner</span>
                        ) : m.is_admin ? (
                          <span className="tag accent">Group admin</span>
                        ) : null}
                      </div>
                      {sub && <div className="item-sub muted">{sub}</div>}
                    </div>
                  </li>
                );
              })}
            </ul>
            {visible.length === 0 && <div className="empty muted">No members match your search.</div>}
          </>
        )}
      </div>
    </section>
  );
}
