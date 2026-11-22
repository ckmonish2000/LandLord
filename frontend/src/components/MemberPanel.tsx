import { useMemo, useState, type ReactNode } from "react";
import { formatPhone } from "../format";
import type { Member } from "../types";
import Avatar from "./Avatar";
import { GroupIcon, SearchIcon } from "./Icons";

/** What the panel header shows: a group, or a property (which is a group). */
export interface PanelSubject {
  name: string;
  pictureUrl?: string | null;
  subtitle?: string;
}

interface Props<M extends Member> {
  subject: PanelSubject | null;
  members: M[] | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  /** Shown when nothing is selected. */
  emptyTitle?: string;
  emptyText?: string;
  /** Button(s) on the right of the header, e.g. "Add as property". */
  headerAction?: ReactNode;
  /** Extra controls on the right of each member row, e.g. floor / house fields. */
  renderMemberExtra?: (m: M) => ReactNode;
}

/** WhatsApp style: saved contact name as title; otherwise the number, with ~push name below. */
export function memberTitle(m: Member): string {
  return m.saved_name || formatPhone(m.phone) || m.push_name || "Hidden number";
}

function memberSubtitle(m: Member): string | null {
  if (m.saved_name) return m.push_name ? `~ ${m.push_name}` : formatPhone(m.phone);
  if (m.phone && m.push_name) return `~ ${m.push_name}`;
  return m.business_name;
}

const rank = (m: Member) => (m.is_super_admin ? 0 : m.is_admin ? 1 : 2);

/** Right column: members of the selected group / property. */
export default function MemberPanel<M extends Member>({
  subject,
  members,
  loading,
  error,
  onRetry,
  emptyTitle = "Select a group",
  emptyText = "Pick a group on the left to see its members.",
  headerAction,
  renderMemberExtra,
}: Props<M>) {
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

  if (!subject) {
    return (
      <section className="detail-panel detail-empty">
        <div className="detail-empty-icon"><GroupIcon size={56} /></div>
        <h2>{emptyTitle}</h2>
        <p className="muted">{emptyText}</p>
      </section>
    );
  }

  return (
    <section className="detail-panel">
      <header className="detail-header">
        <Avatar name={subject.name} src={subject.pictureUrl} kind="group" size={42} />
        <div className="detail-title">
          <h2>{subject.name || "Unnamed group"}</h2>
          {subject.subtitle && <span className="muted small">{subject.subtitle}</span>}
        </div>
        {headerAction && <div className="detail-actions">{headerAction}</div>}
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
                          <span className="tag accent">Group owner</span>
                        ) : m.is_admin ? (
                          <span className="tag accent">Group admin</span>
                        ) : null}
                      </div>
                      {sub && <div className="item-sub muted">{sub}</div>}
                    </div>
                    {renderMemberExtra?.(m)}
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
