import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { House, HouseAssignmentInput, Property, PropertyMember, SavedAssignment } from "../types";
import Avatar from "./Avatar";
import { HouseDetailsModal, MemberDetailsModal } from "./DetailsModals";
import { BuildingIcon, MemberCardIcon, SearchIcon, WarningIcon } from "./Icons";
import { memberSubtitle, memberTitle } from "./MemberPanel";
import { SkeletonList } from "./Skeleton";

interface Props {
  property: Property;
  members: PropertyMember[] | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  onSaved: (saved: SavedAssignment[]) => void;
}

/** What the landlord is editing on one row. */
interface Draft {
  floor: string;
  number: string;
  is_owner: boolean;
  lives_here: boolean;
}

const NO_MEMBERS: PropertyMember[] = [];
const NOTICE_MS = 3000;
const saved = (m: PropertyMember): Draft => ({
  is_owner: m.is_owner,
  lives_here: m.lives_here,
  floor: m.house?.floor ?? "",
  number: m.house?.number ?? "",
});

/** Trim; floor and house number only count for members who live here. */
function normalize(d: Draft): Draft {
  if (!d.lives_here) return { ...d, floor: "", number: "" };
  return { ...d, floor: d.floor.trim(), number: d.number.trim() };
}

const same = (a: Draft, b: Draft) =>
  a.floor === b.floor && a.number === b.number && a.is_owner === b.is_owner && a.lives_here === b.lives_here;

function rowError(d: Draft): string | null {
  const n = normalize(d);
  if (!n.lives_here) return null;
  if (!n.floor && !n.number) return "Add the floor and house number";
  if (!n.floor) return "Add the floor";
  if (!n.number) return "Add the house number";
  return null;
}

/** Assigned members first, by floor then house number; then everyone else by name. */
function bySavedHouse(a: PropertyMember, b: PropertyMember): number {
  if (a.house && b.house) {
    return (
      a.house.floor.localeCompare(b.house.floor, undefined, { numeric: true }) ||
      a.house.number.localeCompare(b.house.number, undefined, { numeric: true }) ||
      memberTitle(a).localeCompare(memberTitle(b))
    );
  }
  if (a.house || b.house) return a.house ? -1 : 1;
  return memberTitle(a).localeCompare(memberTitle(b));
}

const plural = (n: number, one: string, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;

/** Right column for a property: every member with floor, house number, owner and lives here,
 *  saved together from one bar at the bottom. */
export default function PropertyPanel({ property, members, loading, error, onRetry, onSaved }: Props) {
  const [query, setQuery] = useState("");
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [houseOpen, setHouseOpen] = useState<House | null>(null);
  const [memberOpen, setMemberOpen] = useState<PropertyMember | null>(null);

  // "Saved 3 members" fades out on its own.
  useEffect(() => {
    if (!notice) return;
    const id = setTimeout(() => setNotice(null), NOTICE_MS);
    return () => clearTimeout(id);
  }, [notice]);

  const list = members ?? NO_MEMBERS;
  const valueOf = (m: PropertyMember) => drafts[m.jid] ?? saved(m);

  const changed = list.filter((m) => drafts[m.jid] && !same(normalize(drafts[m.jid]), saved(m)));
  const invalid = changed.filter((m) => rowError(drafts[m.jid]));

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const sorted = [...list].sort(bySavedHouse);
    if (!q) return sorted;
    return sorted.filter((m) =>
      [m.saved_name, m.push_name, m.business_name, m.phone, m.house?.floor, m.house?.number].some((v) =>
        v?.toLowerCase().includes(q),
      ),
    );
  }, [list, query]);

  const stats = useMemo(() => {
    const residents = list.filter((m) => m.house);
    return {
      residents: residents.length,
      houses: new Set(residents.map((m) => m.house!.id)).size,
      owners: list.filter((m) => m.is_owner).length,
    };
  }, [list]);

  function edit(m: PropertyMember, patch: Partial<Draft>) {
    setNotice(null);
    setSaveError(null);
    setDrafts((d) => ({ ...d, [m.jid]: { ...(d[m.jid] ?? saved(m)), ...patch } }));
  }

  async function save() {
    if (changed.length === 0 || invalid.length > 0) return;
    setSaving(true);
    setSaveError(null);
    try {
      const items: HouseAssignmentInput[] = changed.map((m) => {
        const d = normalize(drafts[m.jid]);
        return {
          member_jid: m.jid,
          floor: d.lives_here ? d.floor : null,
          number: d.lives_here ? d.number : null,
          is_owner: d.is_owner,
          lives_here: d.lives_here,
        };
      });
      const result = await api.saveAssignments(property.id, items);
      onSaved(result);
      setDrafts({});
      setNotice(`Saved ${plural(result.length, "member")}`);
    } catch (e) {
      setSaveError(e instanceof Error ? `Could not save. ${e.message}` : "Could not save. Try again.");
    } finally {
      setSaving(false);
    }
  }

  const people = (house: House) => list.filter((m) => m.house?.id === house.id);
  const barVisible = changed.length > 0 || notice !== null || saveError !== null;

  return (
    <section className="detail-panel">
      <header className="detail-header">
        <Avatar name={property.name} kind="group" size={40} />
        <div className="detail-title">
          <h2>{property.name || "Unnamed group"}</h2>
          <span className="muted small">
            {members
              ? `${plural(list.length, "member")} · ${plural(stats.houses, "house")} · ${plural(stats.owners, "owner")}`
              : "WhatsApp group"}
          </span>
        </div>
      </header>

      <div className="detail-body">
        <div className="toolbar">
          <label className="search">
            <SearchIcon size={16} />
            <input
              placeholder="Search by name, number, floor or house"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          {members && list.length > 0 && (
            <span className="muted small nowrap">
              {stats.residents} of {list.length} live here
            </span>
          )}
        </div>

        {loading && <SkeletonList rows={7} avatar={36} />}

        {!loading && error && (
          <div className="empty">
            <WarningIcon size={32} className="empty-icon danger" />
            <p className="form-error">{error}</p>
            <button className="btn btn-secondary" onClick={onRetry}>Try again</button>
          </div>
        )}

        {!loading && !error && members && (
          <div className="house-table" role="table" aria-label="Members and their houses">
            <div className="house-row house-head" role="row">
              <span role="columnheader">Member</span>
              <span role="columnheader" className="center">Owner</span>
              <span role="columnheader" className="center">Lives here</span>
              <span role="columnheader">Floor</span>
              <span role="columnheader">House no.</span>
              <span role="columnheader" className="center">Details</span>
            </div>

            {visible.map((m) => {
              const v = valueOf(m);
              const isChanged = changed.includes(m);
              const err = isChanged ? rowError(v) : null;
              const sub = memberSubtitle(m);
              return (
                <div key={m.jid} role="row" className={`house-row ${isChanged ? "changed" : ""} ${err ? "invalid" : ""}`}>
                  <div className="house-member" role="cell">
                    <Avatar name={m.saved_name || m.push_name || m.phone || "?"} src={m.picture_url} size={36} />
                    <div className="item-text">
                      <div className="item-row">
                        <span className="item-title">{memberTitle(m)}</span>
                        {isChanged && <span className="tag accent">Edited</span>}
                      </div>
                      {err ? (
                        <span className="row-error small">{err}</span>
                      ) : (
                        sub && <span className="item-sub muted small">{sub}</span>
                      )}
                    </div>
                  </div>
                  <label role="cell" className="cell-check" title="Owns a house in this property">
                    <input
                      type="checkbox"
                      checked={v.is_owner}
                      onChange={(e) => edit(m, { is_owner: e.target.checked })}
                    />
                    <span className="check-label">Owner</span>
                  </label>
                  <label role="cell" className="cell-check" title="Lives in this property">
                    <input
                      type="checkbox"
                      checked={v.lives_here}
                      onChange={(e) => edit(m, { lives_here: e.target.checked })}
                    />
                    <span className="check-label">Lives here</span>
                  </label>
                  <div role="cell" className="cell-floor">
                    <input
                      className="cell-input"
                      aria-label={`Floor for ${memberTitle(m)}`}
                      placeholder={v.lives_here ? "Floor" : "–"}
                      value={v.lives_here ? v.floor : ""}
                      disabled={!v.lives_here}
                      maxLength={20}
                      onChange={(e) => edit(m, { floor: e.target.value })}
                    />
                  </div>
                  <div role="cell" className="cell-number">
                    <input
                      className="cell-input"
                      aria-label={`House number for ${memberTitle(m)}`}
                      placeholder={v.lives_here ? "House" : "–"}
                      value={v.lives_here ? v.number : ""}
                      disabled={!v.lives_here}
                      maxLength={20}
                      onChange={(e) => edit(m, { number: e.target.value })}
                    />
                  </div>
                  <div role="cell" className="cell-actions">
                    <button
                      className="icon-btn sm"
                      disabled={!m.house || isChanged}
                      title={
                        !m.house
                          ? "Only for members who live here"
                          : isChanged
                            ? "Save your changes first"
                            : `House ${m.house.number} details`
                      }
                      aria-label="House details"
                      onClick={() => m.house && setHouseOpen(m.house)}
                    >
                      <BuildingIcon size={18} />
                    </button>
                    <button
                      className="icon-btn sm"
                      title={`${memberTitle(m)} details`}
                      aria-label="Member details"
                      onClick={() => setMemberOpen(m)}
                    >
                      <MemberCardIcon size={18} />
                    </button>
                  </div>
                </div>
              );
            })}

            {visible.length === 0 && (
              <div className="empty muted">
                {list.length ? "No members match your search." : "This group has no members."}
              </div>
            )}
          </div>
        )}
      </div>

      <div className={`save-bar ${barVisible ? "visible" : ""}`} aria-live="polite">
        <div className="save-bar-inner">
          <span className={`save-status ${saveError || invalid.length ? "error" : ""}`}>
            {saveError
              ? saveError
              : invalid.length
                ? `${plural(invalid.length, "row needs", "rows need")} attention`
                : changed.length
                  ? `${plural(changed.length, "unsaved change")}`
                  : notice}
          </span>
          {changed.length > 0 && (
            <div className="save-actions">
              <button className="btn btn-ghost" onClick={() => setDrafts({})} disabled={saving}>
                Discard
              </button>
              <button className="btn btn-primary" onClick={save} disabled={saving || invalid.length > 0}>
                {saving ? "Saving" : "Save changes"}
              </button>
            </div>
          )}
        </div>
      </div>

      {houseOpen && (
        <HouseDetailsModal
          house={houseOpen}
          property={property}
          people={people(houseOpen)}
          onClose={() => setHouseOpen(null)}
        />
      )}
      {memberOpen && (
        <MemberDetailsModal member={memberOpen} property={property} onClose={() => setMemberOpen(null)} />
      )}
    </section>
  );
}
